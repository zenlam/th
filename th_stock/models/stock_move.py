# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    @api.depends('product_id', 'order_todo_uom')
    def _compute_havi_code(self):
        for move in self:
            if move.product_id and move.order_todo_uom:
                multi_uom_id = self.env['product.multi.uom'].search([
                    ('product_tmpl_id', '=',
                     move.product_id.product_tmpl_id.id),
                    ('name', '=', move.order_todo_uom.id)
                ])
                move.barcode = multi_uom_id.barcode

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=1)
    adn_qty = fields.Float(
        'ADN Qty',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.0,
        help="ADN Qty updated from HAVI Delivery Note 'Qty' column through EDI")
    adn_uom = fields.Many2one('uom.uom', 'ADN UOM')
    order_todo_qty = fields.Float(
        'Order / To Do Qty',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.0,
        help="")
    order_todo_uom = fields.Many2one('uom.uom', 'Order / To Do UOM')
    delivered_received_qty = fields.Float(
        'Delivered / Received QTY',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.0,
        compute = '_delivered_received_qty_compute', inverse = '_delivered_received_qty_set')
    delivered_received_uom = fields.Many2one('uom.uom', 'Delivered / Received UOM')
    remark = fields.Text('Remark')
    temp_line_qty = fields.Float("Temp qty", compute='_temp_line_quantity')
    allow_change_picking_in_uom = fields.Boolean(compute='_get_user_can_change_picking_uom')
    show_details_visible = fields.Boolean('Details Visible', compute='_compute_show_details_visible')
    is_stock_transfer = fields.Boolean(related='picking_id.is_stock_transfer',
                                       string="Is Stock Transfer")
    barcode = fields.Char(string=_('HAVI Code'), compute='_compute_havi_code')
    scrap_picking_id = fields.Many2one('scrap.picking')

    def _prepare_account_move_line(self, qty, cost, credit_account_id,
                                   debit_account_id):
        if self.env.context.get('is_scrap'):
            # take product's Standard Outlet Cost instead of product's Cost
            cost = abs(self.product_id.outlet_standard_price * qty)
        return super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id)

    # def action_show_details(self):
    #     res = super(StockMove, self).action_show_details()
    #     if self.is_stock_transfer:
    #         res['context']['show_lots_m2o'] = False
    #     return res

    def _account_entry_move(self):
        """
        Create account move for internal transfer
        """
        self.ensure_one()
        res = super(StockMove, self)._account_entry_move()
        # Create Journal Entry for products moving within company
        if self._is_internal():
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self._create_account_move_line(acc_valuation, acc_valuation,
                                           journal_id)
        return res

    def _run_valuation(self, quantity=None):
        """
        Run valuation for internal transfer to get the value
        """
        self.ensure_one()
        res = super(StockMove, self)._run_valuation()
        if self._is_internal():
            valued_move_lines = self.move_line_ids.filtered(
                lambda ml: ml.location_id._should_be_valued() and ml.location_dest_id._should_be_valued() and not ml.owner_id)
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, self.product_id.uom_id)
            vals = {}
            price_unit = self.product_id.outlet_standard_price
            value = price_unit * (quantity or valued_quantity)
            vals = {
                'price_unit': price_unit,
                'value': value
            }
            self.write(vals)
        return res

    def _action_done(self):
        """
        To consider internal transfer and create account entry for it
        """
        res = super(StockMove, self)._action_done()
        for move in res.filtered(lambda m: m.product_id.valuation == 'real_time' and m._is_internal()):
            move._account_entry_move()
        return res

    def _is_internal(self):
        """
        Check if the move is within company
        :return: True is the move is internal transfer
        """
        for move_line in self.move_line_ids.filtered(lambda ml: not ml.owner_id):
            if move_line.location_id._should_be_valued() and \
                    move_line.location_dest_id._should_be_valued():
                return True
        return False

    @api.depends('move_line_ids.qty_done', 'move_line_ids.product_uom_id', 'move_line_nosuggest_ids.qty_done')
    def _delivered_received_qty_compute(self):
        """ This field represents the sum of the move lines `delivered_received_qty`.
        """
        for move in self:
            delivered_received_qty = 0
            for move_line in move._get_move_lines():
                if move_line.product_uom_id and move.delivered_received_uom:
                    delivered_received_qty += move_line.product_uom_id.with_context(
                        {'product_tmpl_id': move.product_id.product_tmpl_id.id})._compute_quantity(move_line.qty_done, move.delivered_received_uom,
                                                                                round=False)
            move.delivered_received_qty = delivered_received_qty

    def _delivered_received_qty_set(self):
        delivered_received_qty = self[0].delivered_received_qty  # any call to create will invalidate `move.quantity_done`
        for move in self:
            move_lines = move._get_move_lines()
            if not move_lines:
                if delivered_received_qty:
                    # do not impact reservation here
                    move_line = self.env['stock.move.line'].create(dict(move._prepare_move_line_vals(), delivered_received_qty=delivered_received_qty))
                    move.write({'move_line_ids': [(4, move_line.id)]})
            elif len(move_lines) == 1:
                move_lines[0].delivered_received_qty = delivered_received_qty
            else:
                raise UserError(_("Cannot set the done quantity from this stock move, work directly with the move lines."))

    def _get_user_can_change_picking_uom(self):
        for move in self:
            move.allow_change_picking_in_uom = self.user_has_groups('th_stock.group_allow_to_change_uom_in_stock_picking')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.picking_id.is_stock_transfer is True and self.product_id:
            uom_id = self.env['product.multi.uom'].search([
                ('product_tmpl_id', '=',
                 self.product_id.product_tmpl_id.id),
                ('outlet_ordering', '=', True),
                ('is_default', '=', True)
            ])
            self.order_todo_uom = uom_id.name
            self.delivered_received_uom = uom_id.name
        return super(StockMove, self).onchange_product_id()

    @api.onchange('order_todo_qty', 'order_todo_uom', 'product_id')
    def onchange_order_todo_qty_uom(self):
        if self.product_id:
            self.delivered_received_uom = self.order_todo_uom.id
            if self.order_todo_uom and self.order_todo_qty != 0:
                self.product_uom_qty = self.order_todo_uom.with_context({'product_tmpl_id':self.product_id.product_tmpl_id.id})._compute_quantity(self.order_todo_qty,
                                                                              self.product_uom,
                                                                              rounding_method='HALF-UP')
            else:
                self.product_uom_qty = 0

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """ Create stock move line based on the stock move
        Note: This function will be called from several functions to create stock move line based on stock move values
        """
        res = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        res.update({
            'account_analytic_id': self.account_analytic_id.id,
            'delivered_received_uom' : self.order_todo_uom.id,
            'delivered_received_uom_initial': self.order_todo_uom.id,
        })
        return res
    @api.depends('quantity_done', 'product_uom_qty')
    def _temp_line_quantity(self):
        """ This field is just for the auto populate remaing quantity while adding new line in Detailed Operations wizard.
        """
        for move in self:
            if move.quantity_done > 0:
                temp_qty =  move.product_uom_qty - move.quantity_done
                if temp_qty > 0:
                    move.temp_line_qty = temp_qty


    @api.onchange('delivered_received_qty', 'delivered_received_uom')
    def onchange_delivered_rece_qty_uom_stock_move(self):
        if self.delivered_received_uom != self.order_todo_uom and \
                self.picking_id.is_stock_transfer is False:
            raise ValidationError("Order UOM and Deliver UOM should be same !")

        if self.product_id and self.product_id.tracking == 'none':
            if self.delivered_received_uom and self.delivered_received_qty != 0:
                self.quantity_done = self.delivered_received_uom.with_context({'product_tmpl_id':self.product_id.product_tmpl_id.id})._compute_quantity(self.delivered_received_qty,
                                                                              self.product_uom,
                                                                              rounding_method='HALF-UP')
            else:
                self.quantity_done = 0


    @api.model
    def create(self, vals):
        picking = self.env['stock.picking'].search([
            ('id', '=', vals['picking_id'])])
        if picking.is_stock_transfer is True:
            vals['account_analytic_id'] = \
                picking.location_dest_id.account_analytic_id.id
        if vals.get('sale_line_id'):
            sale_line = self.env['sale.order.line'].browse(vals.get('sale_line_id'))
            vals['order_todo_qty'] = sale_line.product_uom_qty
            vals['order_todo_uom'] = sale_line.product_uom.id
            vals['delivered_received_uom'] = sale_line.product_uom.id
            vals['delivered_received_uom_initial'] = sale_line.product_uom.id
        return super(StockMove, self).create(vals)

    # @api.multi
    # def write(self, vals):
    #     res = super(StockMove, self).write(vals)
    #     if not self.env.context.get('update_self_delivery'):
    #         for move in self:
    #             if move.order_todo_uom:
    #                 delivered_received_uom = move.order_todo_uom.id
    #                 move.with_context({'update_self_delivery':True}).write({'delivered_received_uom':delivered_received_uom})
    #     return res

    @api.depends('product_id', 'has_tracking')
    def _compute_show_details_visible(self):
        """ According to this field, the button that calls `action_show_details` will be displayed
        to work on a move from its picking form view, or not.
        """

        has_package = self.user_has_groups('stock.group_tracking_lot')  # Manage Packages
        multi_locations_enabled = self.user_has_groups('stock.group_stock_multi_locations')  # Manage Multiple Stock Locations
        consignment_enabled = self.user_has_groups('stock.group_tracking_owner')  # Manage Different Stock Owners

        # show_details_visible = multi_locations_enabled or consignment_enabled or has_package
        show_details_visible =  consignment_enabled or has_package
        for move in self:
            if not move.product_id:
                move.show_details_visible = False
            else:
                move.show_details_visible = ((show_details_visible or move.has_tracking != 'none') and
                                             (move.state != 'draft' or (
                                                         move.picking_id.immediate_transfer and move.state == 'draft')) and
                                             move.picking_id.picking_type_id.show_operations is False)

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    allow_change_picking_in_uom = fields.Boolean(compute='_get_user_can_change_picking_uom')
    delivered_received_qty = fields.Float(
        'Received QTY',
        digits=dp.get_precision('Product Unit of Measure'),
        default=0.0,
        help="")
    delivered_received_uom = fields.Many2one('uom.uom', 'Received UOM')
    delivered_received_uom_initial = fields.Many2one('uom.uom', 'Received UOM Initial')

    def _get_user_can_change_picking_uom(self):
        for line in self:
            line.allow_change_picking_in_uom = self.user_has_groups('th_stock.group_allow_to_change_uom_in_stock_picking')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'move_id' in vals and vals.get('move_id'):
                move = self.env['stock.move'].browse(vals['move_id'])
                vals['delivered_received_uom'] = move.delivered_received_uom.id
                vals['delivered_received_uom_initial'] = move.delivered_received_uom.id
        return super(StockMoveLine, self).create(vals_list)

    @api.onchange('delivered_received_qty', 'delivered_received_uom')
    def onchange_delivered_rece_qty_uom(self):
        if self.delivered_received_uom and self.delivered_received_qty != 0:
            self.qty_done = self.delivered_received_uom.with_context(
                {'product_tmpl_id': self.product_id.product_tmpl_id.id})._compute_quantity(
                self.delivered_received_qty,
                self.product_uom_id,
                rounding_method='HALF-UP')
        else:
            self.qty_done = 0

