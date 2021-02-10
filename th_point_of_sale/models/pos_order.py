# -*- coding: utf-8 -*-
from functools import partial

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from openerp.tools import float_round
from datetime import datetime


class PosIngredientLine(models.Model):
    _name = "pos.ingredient.line"
    _description = "Point of Sale Ingredient Lines"
    _rec_name = "product_id"

    def _ingredient_line_fields(self, line, session_id=None):
        if line and 'name' not in line[2]:
            session = self.env['pos.session'].browse(session_id).exists() if session_id else None
            if session and session.config_id.sequence_line_id:
                # set name based on the sequence specified on the config
                line[2]['name'] = session.config_id.sequence_line_id._next()
            else:
                # fallback on any pos.order.line sequence
                line[2]['name'] = self.env['ir.sequence'].next_by_code('pos.order.line')

        if line and 'tax_ids' not in line[2]:
            product = self.env['product.product'].browse(line[2]['product_id'])
            line[2]['tax_ids'] = [(6, 0, [x.id for x in product.taxes_id])]
        return line

    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Line No', required=True, copy=False)
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('sale_ok', '=', True)],
                                 required=True, change_default=True)
    price_unit = fields.Float(string='Unit Price',
                              digits=dp.get_precision('Product Price'))
    standard_price = fields.Float(string='Cost',
                                  digits=dp.get_precision('Product Price'))
    qty = fields.Float('Quantity',
                       digits=dp.get_precision('Product Unit of Measure'),
                       default=1)
    order_id = fields.Many2one('pos.order', string='Order Ref',
                               ondelete='cascade')
    is_extra = fields.Boolean('Extra')
    menu_id = fields.Many2one('product.product', 'Menu Item')
    recovery = fields.Float('Recovery (%)', required=True)
    inv_deduction_qty = fields.Float(compute='_get_inventory_deduction_qty',
                                     string='Inventory Deduction Quantity')

    @api.depends('qty', 'recovery')
    def _get_inventory_deduction_qty(self):
        for rec in self:
            if rec.qty and rec.recovery:
                rec.inv_deduction_qty = rec.qty / (rec.recovery / 100)

    @api.model
    def create(self, values):
        if values.get('order_id') and not values.get('name'):
            # set name based on the sequence specified on the config
            config_id = self.order_id.browse(
                values['order_id']).session_id.config_id.id
            # HACK: sequence created in the same transaction as the config
            # cf TODO master is pos.config create
            # remove me saas-15
            self.env.cr.execute("""
                    SELECT s.id
                    FROM ir_sequence s
                    JOIN pos_config c
                      ON s.create_date=c.create_date
                    WHERE c.id = %s
                      AND s.code = 'pos.ingredient.line'
                    LIMIT 1
                    """, (config_id,))
            sequence = self.env.cr.fetchone()
            if sequence:
                values['name'] = self.env['ir.sequence'].browse(
                    sequence[0])._next()
        if not values.get('name'):
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code(
                'pos.order.line')
        return super(PosIngredientLine, self).create(values)

    @api.onchange('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _onchange_amount_line_all(self):
        for line in self:
            res = line._compute_amount_line_all()
            line.update(res)

    def _compute_amount_line_all(self):
        self.ensure_one()
        fpos = self.order_id.fiscal_position_id
        tax_ids_after_fiscal_position = fpos.map_tax(self.tax_ids, self.product_id, self.order_id.partner_id) if fpos else self.tax_ids
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = tax_ids_after_fiscal_position.compute_all(price, self.order_id.pricelist_id.currency_id, self.qty, product=self.product_id, partner=self.order_id.partner_id)
        return {
            'price_subtotal_incl': taxes['total_included'],
            'price_subtotal': taxes['total_excluded'],
        }

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(
                    _('You have to select a pricelist in the sale form !\n'
                      'Please set one before choosing a product.'))
            price = self.order_id.pricelist_id.get_product_price(
                self.product_id, self.qty or 1.0, self.order_id.partner_id)
            self._onchange_qty()
            self.tax_ids = self.product_id.taxes_id.filtered(
                lambda r: not self.company_id or
                          r.company_id == self.company_id)
            fpos = self.order_id.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(
                self.tax_ids, self.product_id,
                self.order_id.partner_id) if fpos else self.tax_ids
            self.price_unit = self.env[
                'account.tax']._fix_tax_included_price_company(
                price, self.product_id.taxes_id,
                tax_ids_after_fiscal_position, self.company_id)

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(
                    _('You have to select a pricelist in the sale form.'))
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if (self.product_id.taxes_id):
                taxes = self.product_id.taxes_id.compute_all(
                    price, self.order_id.pricelist_id.currency_id,
                    self.qty, product=self.product_id, partner=False)
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']

    @api.multi
    def _get_tax_ids_after_fiscal_position(self):
        for line in self:
            line.tax_ids_after_fiscal_position = \
                line.order_id.fiscal_position_id.map_tax(
                    line.tax_ids, line.product_id, line.order_id.partner_id)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):

        lines = []
        if ui_order.get('lines'):
            for l in ui_order['lines']:
                lines.append(l)
                if l[2].get('menu_datas'):
                    for menu in l[2]['menu_datas']:
                        lines.append(menu)
            ui_order['lines'] = lines

        res = super(PosOrder, self)._order_fields(ui_order)
        process_ingredient_line = partial(
            self.env['pos.ingredient.line']._ingredient_line_fields,
            session_id=ui_order['pos_session_id'])
        res.update({
            'ingredient_lines': [process_ingredient_line(l) for l in ui_order['ingredient_lines']] if ui_order['ingredient_lines'] else False
        })
        return res

    ingredient_lines = fields.One2many('pos.ingredient.line', 'order_id',
                                       string='Ingredient Lines',
                                       states={'draft': [('readonly', False)]},
                                       readonly=True, copy=True)
    is_refund = fields.Boolean(string='Is Refund', default=False, help="Is Refund Order")
    is_refunded = fields.Boolean(string='Is Refunded', default=False, help="Is Order Refunded")
    refund_order_id = fields.Many2one(comodel_name='pos.order', help='Refund receipt')
    outlet_id = fields.Many2one('stock.warehouse', related='config_id.outlet_id', string='Outlet', store=True)

    # NOTE: stop creating picking for each order. (this has been moved to pos session close)
    @api.multi
    def action_pos_order_paid(self):
        if not self.test_paid():
            raise UserError(_("Order is not paid."))
        self.write({'state': 'paid'})
        # return self.create_picking()
        return True

    def _prepare_analytic_account(self, line):
        ''' This method is designed to be inherited in a custom module
        Note: This function will return analytic account id to create invoice line and create account move line
        '''
        return line.order_id.session_id.config_id.outlet_id.analytic_account_id.id

    def prepare_picking_vals(self, order, picking_type, location_id, destination_id):
        """ This will return the picking values dictionary to function create_picking
        """
        address = order.partner_id.address_get(['delivery']) or {}
        return {
            'origin': order.name,
            'partner_id': address.get('delivery', False),
            'date_done': order.date_order,
            'picking_type_id': picking_type.id,
            'company_id': order.company_id.id,
            'move_type': 'direct',
            'note': order.note or "",
            'location_id': location_id,
            'location_dest_id': destination_id,
        }

    def prepare_move_vals(self, line, order, order_picking, return_picking, picking_type, return_pick_type,
                          location_id, destination_id):
        """ This will return the moves values dictionary to function create_picking
        """
        # need to pass the analytic account from the outlet to pos moves
        analytic_account_id = order.session_id.config_id.outlet_id.analytic_account_id
        return {
            'name': line.name,
            'product_uom': line.product_id.uom_id.id,
            'picking_id': order_picking.id if line.inv_deduction_qty >= 0 else return_picking.id,
            'picking_type_id': picking_type.id if line.inv_deduction_qty >= 0 else return_pick_type.id,
            'product_id': line.product_id.id,
            'product_uom_qty': abs(line.inv_deduction_qty),
            'state': 'draft',
            'location_id': location_id if line.inv_deduction_qty >= 0 else destination_id,
            'location_dest_id': destination_id if line.inv_deduction_qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
            'account_analytic_id': analytic_account_id.id,
        }

    def create_picking(self):
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        # If no email is set on the user, the picking creation and validation will fail be cause of
        # the 'Unable to log message, please configure the sender's email address.' error.
        # We disable the tracking in this case.
        if not self.env.user.partner_id.email:
            Picking = Picking.with_context(tracking_disable=True)
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.ingredient_lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                continue
            picking_type = order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = order.location_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            if picking_type:
                message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
                picking_vals = self.prepare_picking_vals(order, picking_type, location_id, destination_id)
                pos_qty = any([x.inv_deduction_qty > 0 for x in order.ingredient_lines if x.product_id.type in ['product', 'consu']])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    if self.env.user.partner_id.email:
                        order_picking.message_post(body=message)
                    else:
                        order_picking.sudo().message_post(body=message)
                neg_qty = any([x.inv_deduction_qty < 0 for x in order.ingredient_lines if x.product_id.type in ['product', 'consu']])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    if self.env.user.partner_id.email:
                        return_picking.message_post(body=message)
                    else:
                        return_picking.message_post(body=message)

            for line in order.ingredient_lines.filtered(
                    lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.inv_deduction_qty,
                                                                                              precision_rounding=l.product_id.uom_id.rounding)):
                move_vals = self.prepare_move_vals(line, order, order_picking, return_picking, picking_type,
                                                   return_pick_type, location_id, destination_id)
                moves |= Move.create(move_vals)

            # prefer associating the regular order picking, not the return
            order.write({'picking_id': order_picking.id or return_picking.id})

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                moves._action_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

        return True

    # NOTE : comment the self.ensure_one() by overwriting full method.
    def _force_picking_done(self, picking):
        """Force picking in order to be set as done."""
        #self.ensure_one()
        picking.action_assign()
        # NOTE use self[0] because all order have only one picking. and set_pack_operation_lot loop through all order and its move so it will wrong.
        wrong_lots = self[0].set_pack_operation_lot(picking)
        if not wrong_lots:
            picking.action_done()

    def _prepare_account_move_and_lines(self, session=None, move=None):
        """ This function will create account move line for each pos order line.
        Note: Need to override the whole function due to the inner function
        """
        def _flatten_tax_and_children(taxes, group_done=None):
            children = self.env['account.tax']
            if group_done is None:
                group_done = set()
            for tax in taxes.filtered(lambda t: t.amount_type == 'group'):
                if tax.id not in group_done:
                    group_done.add(tax.id)
                    children |= _flatten_tax_and_children(tax.children_tax_ids, group_done)
            return taxes + children

        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        IrProperty = self.env['ir.property']
        ResPartner = self.env['res.partner']

        if session and not all(session.id == order.session_id.id for order in self):
            raise UserError(_('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False
        rounding_method = session and session.config_id.company_id.tax_calculation_rounding_method

        def add_anglosaxon_lines(grouped_data):
            Product = self.env['product.product']
            Analytic = self.env['account.analytic.account']
            for product_key in list(grouped_data.keys()):
                if product_key[0] == "product":
                    line = grouped_data[product_key][0]
                    product = Product.browse(line['product_id'])
                    # In the SO part, the entries will be inverted by function compute_invoice_totals
                    price_unit = self._get_pos_anglo_saxon_price_unit(product, line['partner_id'], line['quantity'])
                    account_analytic = Analytic.browse(line.get('analytic_account_id'))
                    res = Product._anglo_saxon_sale_move_lines(
                        line['name'], product, product.uom_id, line['quantity'], price_unit,
                            fiscal_position=order.fiscal_position_id,
                            account_analytic=account_analytic)
                    if res:
                        line1, line2 = res
                        line1 = Product._convert_prepared_anglosaxon_line(line1, line['partner_id'])
                        insert_data('counter_part', {
                            'name': line1['name'],
                            'account_id': line1['account_id'],
                            'credit': line1['credit'] or 0.0,
                            'debit': line1['debit'] or 0.0,
                            'partner_id': line1['partner_id'],
                            # need to pass analytic account value for creating account move line
                            'analytic_account_id': line1['analytic_account_id']
                        })

                        line2 = Product._convert_prepared_anglosaxon_line(line2, line['partner_id'])
                        insert_data('counter_part', {
                            'name': line2['name'],
                            'account_id': line2['account_id'],
                            'credit': line2['credit'] or 0.0,
                            'debit': line2['debit'] or 0.0,
                            'partner_id': line2['partner_id'],
                            # need to pass analytic account value for creating account move line
                            'analytic_account_id': line2['analytic_account_id']
                        })

        for order in self.filtered(lambda o: not o.account_move or o.state == 'paid'):
            current_company = order.sale_journal.company_id
            account_def = IrProperty.get(
                'property_account_receivable_id', 'res.partner')
            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
            if move is None:
                # Create an entry for the sale
                journal_id = self.env['ir.config_parameter'].sudo().get_param(
                    'pos.closing.journal_id_%s' % current_company.id, default=order.sale_journal.id)
                move = self._create_account_move(
                    order.session_id.start_at, order.name, int(journal_id), order.company_id.id)

            def insert_data(data_type, values):
                # if have_to_group_by:
                values.update({
                    'move_id': move.id,
                })

                key = self._get_account_move_line_group_data_type_key(data_type, values, {'rounding_method': rounding_method})
                if not key:
                    return

                grouped_data.setdefault(key, [])

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        current_value = grouped_data[key][0]
                        current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                        if 'currency_id' in values:
                            current_value['amount_currency'] = current_value.get('amount_currency', 0.0) + values.get('amount_currency', 0.0)
                        if key[0] == 'tax' and rounding_method == 'round_globally':
                            if current_value['debit'] - current_value['credit'] > 0:
                                current_value['debit'] = current_value['debit'] - current_value['credit']
                                current_value['credit'] = 0
                            else:
                                current_value['credit'] = current_value['credit'] - current_value['debit']
                                current_value['debit'] = 0

                else:
                    grouped_data[key].append(values)

            # because of the weird way the pos order is written, we need to make sure there is at least one line,
            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
            # are set inside the for loop)
            # TOFIX: a deep refactoring of this method (and class!) is needed
            # in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line
            cur = order.pricelist_id.currency_id
            cur_company = order.company_id.currency_id
            amount_cur_company = 0.0
            date_order = order.date_order.date() if order.date_order else fields.Date.today()
            for line in order.lines:
                if cur != cur_company:
                    amount_subtotal = cur._convert(line.price_subtotal, cur_company, order.company_id, date_order)
                else:
                    amount_subtotal = line.price_subtotal

                # Search for the income account
                if line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))

                name = line.product_id.name
                if line.notice:
                    # add discount reason in move
                    name = name + ' (' + line.notice + ')'

                # Create a move for the line for the order line
                # Just like for invoices, a group of taxes must be present on this base line
                # As well as its children
                base_line_tax_ids = _flatten_tax_and_children(line.tax_ids_after_fiscal_position).filtered(lambda tax: tax.type_tax_use in ['sale', 'none'])
                data = {
                    'name': name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': income_account,
                    'analytic_account_id': self._prepare_analytic_account(line),
                    'credit': ((amount_subtotal > 0) and amount_subtotal) or 0.0,
                    'debit': ((amount_subtotal < 0) and -amount_subtotal) or 0.0,
                    'tax_ids': [(6, 0, base_line_tax_ids.ids)],
                    'partner_id': partner_id
                }
                if cur != cur_company:
                    data['currency_id'] = cur.id
                    data['amount_currency'] = -abs(line.price_subtotal) if data.get('credit') else abs(line.price_subtotal)
                    amount_cur_company += data['credit'] - data['debit']
                insert_data('product', data)

                # Create the tax lines
                taxes = line.tax_ids_after_fiscal_position.filtered(lambda t: t.company_id.id == current_company.id)
                if not taxes:
                    continue
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                for tax in taxes.compute_all(price, cur, line.qty)['taxes']:
                    if cur != cur_company:
                        round_tax = False if rounding_method == 'round_globally' else True
                        amount_tax = cur._convert(tax['amount'], cur_company, order.company_id, date_order, round=round_tax)
                        # amount_tax = cur.with_context(date=date_order).compute(tax['amount'], cur_company, round=round_tax)
                    else:
                        amount_tax = tax['amount']
                    data = {
                        'name': _('Tax') + ' ' + tax['name'],
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'account_id': tax['account_id'] or income_account,
                        'credit': ((amount_tax > 0) and amount_tax) or 0.0,
                        'debit': ((amount_tax < 0) and -amount_tax) or 0.0,
                        'tax_line_id': tax['id'],
                        'partner_id': partner_id,
                        'order_id': order.id,
                        # need to pass analytic account value for creating tax account move line
                        'analytic_account_id': order.session_id.config_id.outlet_id.analytic_account_id.id,
                    }
                    if cur != cur_company:
                        data['currency_id'] = cur.id
                        data['amount_currency'] = -abs(tax['amount']) if data.get('credit') else abs(tax['amount'])
                        amount_cur_company += data['credit'] - data['debit']
                    insert_data('tax', data)

            # round tax lines per order
            if rounding_method == 'round_globally':
                for group_key, group_value in grouped_data.items():
                    if group_key[0] == 'tax':
                        for line in group_value:
                            line['credit'] = cur_company.round(line['credit'])
                            line['debit'] = cur_company.round(line['debit'])
                            if line.get('currency_id'):
                                line['amount_currency'] = cur.round(line.get('amount_currency', 0.0))

            # counterpart
            if cur != cur_company:
                # 'amount_cur_company' contains the sum of the AML converted in the company
                # currency. This makes the logic consistent with 'compute_invoice_totals' from
                # 'account.invoice'. It ensures that the counterpart line is the same amount than
                # the sum of the product and taxes lines.
                amount_total = amount_cur_company
            else:
                amount_total = order.amount_total
            data = {
                'name': _("Trade Receivables"),  # order.name,
                'account_id': order_account,
                'credit': ((amount_total < 0) and -amount_total) or 0.0,
                'debit': ((amount_total > 0) and amount_total) or 0.0,
                'partner_id': partner_id,
                # need to pass analytic account value for creating counterpart account move line
                'analytic_account_id': order.session_id.config_id.outlet_id.analytic_account_id.id,
            }
            if cur != cur_company:
                data['currency_id'] = cur.id
                data['amount_currency'] = -abs(order.amount_total) if data.get('credit') else abs(order.amount_total)
            insert_data('counter_part', data)

            order.write({'state': 'done', 'account_move': move.id})

        if self and order.company_id.anglo_saxon_accounting:
            add_anglosaxon_lines(grouped_data)

        return {
            'grouped_data': grouped_data,
            'move': move,
        }

    def prepare_stock_move_line_vals(self, move, pack_lot):
        """ This will return the stock move line values dictionary to function set_pack_operation_lot
        """
        lot_id, qty = pack_lot['lot_id'], pack_lot['qty']
        return {
            'picking_id': move.picking_id.id,
            'move_id': move.id,
            'product_id': move.product_id.id,
            'product_uom_id': move.product_uom.id,
            'qty_done': qty,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
            'lot_id': lot_id,
            # need to pass account analytic id to stock move line
            'account_analytic_id': move.account_analytic_id.id,
        }

    def set_pack_operation_lot(self, picking=None):
        """Set Serial/Lot number in pack operations to mark the pack operation done.
        Note: Need to override the whole function due to the creation is in the middle of function
        """
        StockProductionLot = self.env['stock.production.lot']
        PosPackOperationLot = self.env['pos.pack.operation.lot']
        has_wrong_lots = False

        for order in self:
            for move in (picking or self.picking_id).move_lines:
                picking_type = (picking or self.picking_id).picking_type_id
                is_manual_lot = False
                lots_necessary = True
                if picking_type:
                    lots_necessary = picking_type and picking_type.use_existing_lots
                qty_done = 0
                pack_lots = []
                pos_pack_lots = PosPackOperationLot.search([('order_id', '=', order.id), ('product_id', '=', move.product_id.id)])
                # print ("===pos_pack_lots",pos_pack_lots)

                if pos_pack_lots and lots_necessary:
                    for pos_pack_lot in pos_pack_lots:
                        stock_production_lot = StockProductionLot.search([('name', '=', pos_pack_lot.lot_name), ('product_id', '=', move.product_id.id)])
                        if stock_production_lot:
                            # a serialnumber always has a quantity of 1 product, a lot number takes the full quantity of the order line
                            qty = 1.0
                            if stock_production_lot.product_id.tracking == 'lot':
                                qty = abs(pos_pack_lot.pos_order_line_id.qty)
                            qty_done += qty
                            pack_lots.append({'lot_id': stock_production_lot.id, 'qty': qty})
                        else:
                            has_wrong_lots = True
                elif move.product_id.tracking == 'none' or not lots_necessary:
                    qty_done = move.product_uom_qty
                elif not pos_pack_lots and lots_necessary and move.product_id.tracking == 'lot':
                    total_lot_qty = 0
                    for move_line in move.move_line_ids.filtered(lambda x: x.lot_id):
                        move_line.write({'qty_done': move_line.product_qty, 'delivered_received_qty': move_line.product_qty})
                        total_lot_qty += abs(move_line.product_qty)
                    remaining_qty = float_round(move.product_qty - total_lot_qty, precision_rounding=move.product_uom.rounding)
                    qty_done += total_lot_qty

                    if remaining_qty:
                        # In case there there is no stock left then negative quant is created, it should be place under negative lot
                        self.generate_lot_negative(move.product_id, move, remaining_qty)
                        qty_done += remaining_qty

                    is_manual_lot = True

                else:
                    has_wrong_lots = True
                for pack_lot in pack_lots:
                    new_move_line_vals = self.prepare_stock_move_line_vals(move, pack_lot)
                    self.env['stock.move.line'].create(new_move_line_vals)
                # print("=========== check if", move.product_qty,qty_done, not pack_lots  , not float_is_zero(qty_done, precision_rounding=move.product_uom.rounding), not is_manual_lot, move._get_move_lines())
                if not pack_lots and not float_is_zero(qty_done, precision_rounding=move.product_uom.rounding) and not is_manual_lot:

                    if len(move._get_move_lines()) < 2:
                        # print("=========== not moveline < 2")
                        move.quantity_done = qty_done
                    else:
                        # print("else move line > 2")
                        move._set_quantity_done(qty_done)

        return has_wrong_lots

    def generate_lot_negative(self, product, move, qty):
        """
        Generate negative lot for product
        :param product:
        :param move:
        :param qty:
        :return:
        """
        lot_name = 'Negative Quantity'
        new_lot_id = self.env['stock.production.lot'].search([('name', '=', lot_name), ('product_id', '=', product.id)], limit=1)
        if not new_lot_id:
            lot_vals = {
                'product_id': product.id,
                'name': lot_name,
                'removal_date': datetime.now()
            }
            new_lot_id = self.env['stock.production.lot'].create(lot_vals)

        neg_lot_stock_move_line = self.env['stock.move.line'].search(([('lot_id', '=', new_lot_id.id), ('move_id', '=', move.id)]))
        if not neg_lot_stock_move_line:
            print ("------------((( Craete negative move line )))------------")
            self.env['stock.move.line'].create(self._prepare_negative_move_line_vals(new_lot_id, move, qty))
        else:
            new_qty = neg_lot_stock_move_line.qty_done + qty
            neg_lot_stock_move_line.write({'qty_done': new_qty, 'product_uom_qty': new_qty, 'delivered_received_qty': new_qty})

    def _prepare_negative_move_line_vals(self, new_lot_id, move, qty):
        return {
            'lot_id': new_lot_id.id or False,
            'move_id': move.id,
            'qty_done': qty,
            'product_uom_qty': qty,
            'delivered_received_uom': move.product_uom.id,
            'delivered_received_uom_initial': move.product_uom.id,
            'delivered_received_qty': qty,
            'product_id': move.product_id.id,
            'product_uom_id': move.product_uom.id,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
            'picking_id': move.picking_id.id,
            'account_analytic_id': move.account_analytic_id.id,
        }

    @api.multi
    def refund(self):
        """Create a copy of order  for refund order"""
        PosOrder = self.env['pos.order']

        for order in self:
            current_session = self.env['pos.session'].search([('state', '!=', 'closed'),
                                                              ('user_id', '=', self.env.uid),
                                                              ('config_id.outlet_id', '=', order.outlet_id.id)
                                                              ],
                                                             limit=1)
            if not current_session:
                raise UserError(
                    _('To return product(s), you need to open a session that will be used to register the refund.'))

            if order.is_refund or order.is_refunded:
                raise UserError(_("This receipt is already cancelled, please check your order list again!"))
            clone = order.copy({
                # ot used, name forced by create
                'name': order.name + _(' REFUND'),
                'session_id': current_session.id,
                'date_order': fields.Datetime.now(),
                'pos_reference': 'REFUND ' + order.pos_reference,
                'lines': False,
                'ingredient_lines': False,
                'amount_tax': -order.amount_tax,
                'amount_total': -order.amount_total,
                'amount_paid': 0,
                'is_refund' : True
            })
            for line in order.lines:
                clone_line = line.copy({
                    # required=True, copy=False
                    'name': line.name + _(' REFUND'),
                    'order_id': clone.id,
                    'qty': -line.qty,
                    'price_subtotal': -line.price_subtotal,
                    'price_subtotal_incl': -line.price_subtotal_incl,
                })

            for line in order.ingredient_lines:
                clone_line = line.copy({
                    # required=True, copy=False
                    'name': line.name + _(' REFUND'),
                    'order_id': clone.id,
                    'qty': -line.qty,
                    'price_unit' : -line.price_unit
                })
            PosOrder += clone

            if order.account_move:
                order.write({'is_refunded': True, 'refund_order_id': clone.id, 'state': 'done'})
            else:
                order.write({'is_refunded': True, 'refund_order_id': clone.id, 'state': 'paid'})

        return {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': PosOrder.ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


