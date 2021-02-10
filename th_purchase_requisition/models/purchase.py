# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_request_ids = fields.One2many('purchase.request', 'purchase_order_id', string="Purchase Requests")
    pr_count = fields.Integer(compute='_compute_purchase_request_count', string='Purchase request count', default=0, store=True)
    purchase_request_order_line = fields.One2many(comodel_name="purchase.order.line",related="order_line", string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=False, readonly=False)

    @api.depends('purchase_request_ids')
    def _compute_purchase_request_count(self):
        for order in self:
            order.pr_count = len(order.purchase_request_ids)

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        for record in self.purchase_request_ids:
            if record.partner_id.id != self.partner_id.id:
                raise ValidationError("Vendor Must be the same in Purchase Request and Purchase Order !")
        return super(PurchaseOrder, self).onchange_partner_id()

    @api.multi
    def action_view_purchase_request(self):
        """ This function returns an action that display existing PR orders of given PR order ids. When only one found, show the PR immediately.
        """
        action = self.env.ref('th_purchase_requisition.action_validated_purchase_request')
        result = action.read()[0]
        result['context'] = {}
        pr_ids = self.mapped('purchase_request_ids')
        # choose the view_mode accordingly
        if not pr_ids or len(pr_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pr_ids.ids)
        elif len(pr_ids) == 1:
            res = self.env.ref('th_purchase_requisition.view_purchase_request_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pr_ids.id
        return result

    @api.multi
    def validate_pr_product_qty(self):
        """
        Add Validation for Purchase Request generated PO.
        if qty for each product in PO is not match with PR then do not allow.
        """
        for po in self:
            if len(po.purchase_request_ids) > 0:
                pr_qty_dict = {}
                pr_product_uom = {} # here each line with same product have same UOM
                for purhase_request in po.purchase_request_ids:
                    for line in purhase_request.purchase_request_line_ids:
                        if line.product_id.id not in pr_product_uom.keys():
                            pr_product_uom[line.product_id.id] = line.order_uom_id
                        if line.product_id.id not in pr_qty_dict.keys():
                            pr_qty_dict[line.product_id.id] = line.order_qty
                        else:
                            pr_qty_dict[line.product_id.id] += line.order_qty

                po_product_ids = {}
                for po_line in po.order_line:
                    compare_qty = 0.0
                    if po_line.product_id.id in pr_product_uom.keys() and po_line.product_uom.id == pr_product_uom[
                        po_line.product_id.id].id:
                        compare_qty = po_line.product_qty
                    else:
                        compare_qty = po_line.product_uom.with_context(
                            {'product_tmpl_id': po_line.product_id.product_tmpl_id.id})._compute_quantity(
                            po_line.product_qty, pr_product_uom[po_line.product_id.id], rounding_method='HALF-UP')

                    if po_line.product_id.id not in po_product_ids.keys():
                        po_product_ids[po_line.product_id.id] = compare_qty
                    else:
                        po_product_ids[po_line.product_id.id] += compare_qty

                mismatch_message = 'Following Products quantity mismatch with the PR. \n'
                raise_mismatch = False
                for p_id in pr_qty_dict:

                    if p_id in po_product_ids:
                        if pr_qty_dict[p_id] != po_product_ids[p_id]:
                            raise_mismatch = True
                            mismatch_message += "\n Product : '%s' [ Requested Quantity : %s (%s), Purchase Order Quantity : %s (%s) ]"%(
                             self.env['product.product'].browse(p_id).name,
                             pr_qty_dict[p_id],
                             pr_product_uom[p_id].name,
                             po_product_ids[p_id],
                             pr_product_uom[p_id].name
                            )
                    else:
                        if pr_qty_dict[p_id] > 0:
                            raise ValidationError('Missing product %s found in Purchase Request which is not in Purchase Order !' %
                                                  (self.env['product.product'].browse(p_id).name))
                if raise_mismatch:
                    raise ValidationError(mismatch_message)

                extra_products = []
                for p_id in po_product_ids:
                    if p_id not in pr_qty_dict:
                        extra_products.append(self.env['product.product'].browse(p_id).name)
                if extra_products:
                    raise ValidationError("Following Extra product(s) found in Purchase Order which is(are) not in Purchase Request ! \n\n %s"%(", ".join(x for x in extra_products)))

    @api.multi
    def button_confirm(self):
        # validation for the purchase request related PO
        self.validate_pr_product_qty()
        res = super(PurchaseOrder, self).button_confirm()
        for po in self:
            if po.purchase_request_ids:
                po.purchase_request_ids.write({'state' : 'po_confirm',
                                               'po_confirm_user_id' :  self.env.user.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        self.validate_pr_product_qty()
        return res

    @api.multi
    def button_cancel(self):
        result = super(PurchaseOrder, self).button_cancel()
        for po in self:
            if po.purchase_request_ids:
                po.purchase_request_ids.write({'state': 'po_cancel',
                                               'po_cancelled_user_id': self.env.user.id})
        return result

    @api.multi
    def _create_picking(self):
        for order in self:
            if len(order.purchase_request_ids) > 0:
                order._custom_create_picking()
            else:
                super(PurchaseOrder, order)._create_picking()
        return True

    @api.model
    def _custom_prepare_picking(self, purchase_request):
        # _custom_prepare_picking method is only called when this PO is generated from the PR
        if not purchase_request:
            raise ValidationError("Missing Purchase request !")
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)

        picking_type_id = False
        if purchase_request.outlet_id.in_type_id:
            picking_type_id = purchase_request.outlet_id.in_type_id

        if not picking_type_id:
            raise ValidationError("There is no Receipt Operation type available for %s"%purchase_request.outlet_id.name)

        return {
            'picking_type_id': picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            'purchase_request_id' : purchase_request.id
        }

    @api.multi
    def _custom_create_picking(self):
        # _custom_create_picking method is only called when this PO is generated from the PR
        StockPicking = self.env['stock.picking']
        for order in self:
            pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            if pickings:
                raise ValidationError(
                    "This PO is generated from PR and it seems this PO already have confirmed before !")

            for pr_record in order.purchase_request_ids:

                if any([ptype in ['product', 'consu'] for ptype in pr_record.purchase_request_line_ids.mapped('product_id.type')]):
                    res = order._custom_prepare_picking(pr_record)
                    picking = StockPicking.create(res)
                    moves = order.order_line._custom_create_stock_moves(picking, pr_record)
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date_expected):
                        seq += 5
                        move.sequence = seq
                    moves._action_assign()
                    picking.message_post_with_view('mail.message_origin_link',
                                                   values={'self': picking, 'origin': order},
                                                   subtype_id=self.env.ref('mail.mt_note').id)
        return True



class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    old_product_uom = fields.Many2one('uom.uom', string='Old Product Unit of Measure')


    @api.multi
    def _custom_create_stock_moves(self, picking, pr_record):
        # _custom_create_stock_moves method is only called when this PO is generated from the PR
        values = []
        for line in self:
            for val in line.with_context({'purchase_request_id':pr_record.id})._prepare_stock_moves(picking):
                values.append(val)
        return self.env['stock.move'].create(values)

    @api.multi
    def _prepare_stock_moves(self, picking):
        self.ensure_one()
        if len(self.order_id.purchase_request_ids) > 0:
            res = self._custom_prepare_stock_moves(picking)
        else:
            res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        return res

    @api.multi
    def _custom_prepare_stock_moves(self, picking):
        if not self.env.context.get('purchase_request_id'):
            raise ValidationError("Purchase Request is missing !")
        pr_record = self.env['purchase.request'].browse(self.env.context['purchase_request_id'])

        # this is custom prepare stock move which is only for the PO which created from the PR
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        # qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        # NOTE: Mitesh : bellow part no need as each PR hase their own Picking so you will find other moves but we should not consider those move qty to deduct
        # for move in self.move_ids.filtered(
        #         lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
        #     qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': picking.picking_type_id.default_location_dest_id.id, #self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'outlet_std_price_unit' : self.product_id.outlet_standard_price,
            'picking_type_id': picking.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'route_ids': picking.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in picking.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
            'account_analytic_id': picking.picking_type_id.default_location_dest_id.account_analytic_id.id,
        }
        #diff_quantity = self.product_qty - qty
        diff_quantity = 0.0
        pr_uom = False
        for pr_line in pr_record.purchase_request_line_ids:
            if self.product_id.id == pr_line.product_id.id:
                # if self.product_uom.id != pr_line.order_uom_id.id:
                #     raise ValidationError("UOM are Different for product : %s ! \n"
                #                           "Purchase request : %s product UOM (%s) and Purchase order UOM (%s)."
                #                           %(pr_line.product_id.name,
                #                             pr_record.name,
                #                             pr_line.order_uom_id.name,
                #                             self.product_uom.name))
                diff_quantity += pr_line.order_qty
                pr_uom = pr_line.order_uom_id


        # Custom field of stock.move
        template['order_todo_qty'] = diff_quantity
        template['order_todo_uom'] = pr_uom.id
        template['delivered_received_uom'] = pr_uom.id
        template['delivered_received_uom_initial'] = pr_uom.id

        # NOTE here we use PR UOM to convert the quantity in case uom is different then the base UOM
        if float_compare(diff_quantity, 0.0, precision_rounding=pr_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if pr_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = pr_uom.with_context({'product_tmpl_id':self.product_id.product_tmpl_id.id})._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = diff_quantity
            res.append(template)
        return res

    @api.multi
    def button_delete_po_line(self):
        for record in self:
            if record.order_id.state in ['purchase','done','cancel']:
                raise ValidationError('You can not delete line which is already confirmed or done !')
            if len(record.order_id.purchase_request_ids) > 0:
                # open wizard and unlink all PR same product line
                action = self.env.ref('th_purchase_requisition.action_wizard_po_line_delete').read()[0]
                return action
            else:
                record.unlink()

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if len(self.order_id.purchase_request_ids) > 0:
            if self.product_qty and self.product_uom:
                self.product_qty = self.old_product_uom.with_context({'product_tmpl_id':self.product_id.product_tmpl_id.id})._compute_quantity(self.product_qty, self.product_uom, rounding_method='HALF-UP')
        self.old_product_uom = self.product_uom.id
        return super(PurchaseOrderLine, self)._onchange_quantity()

