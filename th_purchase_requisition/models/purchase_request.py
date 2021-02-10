# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class PurchaseRequest(models.Model):
    _name = "purchase.request"
    _inherit = ['mail.thread']


    name = fields.Char('Purchase Request Number', copy=False, required=True, default=lambda self: _('New'))
    state = fields.Selection([('draft', "Draft"),
                              ('pending_approval', "Pending Approval"),
                              ('mgr_approve', "Mgr Approval"),
                              ('request_reject', "Request Reject"),
                              ('po_raised', "PO Raised"),
                              ('po_confirm', "PO Confirm"),
                              ('po_cancel', "PO Cancel"),
                              ('done', "Done"),
                              ('cancel', "Cancel")
                              ], string="State", default='draft', track_visibility='onchange')
    requestor_id = fields.Many2one('res.users', string='Requester', default= lambda self: self.env.user)
    outlet_id = fields.Many2one('stock.warehouse', domain=[('is_outlet','=',True)], string='Outlet', required=True)
    partner_id = fields.Many2one('res.partner', domain=[('supplier','=',True)], required=True, string="Vendor")
    pur_request_tmpl_id = fields.Many2one('purchase.request.tmpl', required=True, string="Purchase Request Template", track_visibility='onchange')
    request_delivery_date = fields.Date('Request Delivery Date', required=True, copy=False)
    submission_date = fields.Date('Submission Date', track_visibility='onchange', copy=False)
    approval_date = fields.Date('Approval Date', track_visibility='onchange', copy=False)
    stock_coverage_day = fields.Integer('Stock Coverage Day (days)', required=True)
    eta_on_submission_date = fields.Date('ETA based on Submission Date', copy=False)
    eta_on_approval_date = fields.Date('ETA based on Approval Date:', copy=False)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase', copy=False, ondelete='restrict')
    po_raise_user_id = fields.Many2one('res.users', 'PO Raised By', copy=False)
    po_confirm_user_id = fields.Many2one('res.users', 'PO Confirm By', copy=False)
    po_cancelled_user_id = fields.Many2one('res.users', 'PO Cancelled By', copy=False)
    cancelled_user_id = fields.Many2one('res.users', 'Cancelled By', copy=False)
    rejected_user_id = fields.Many2one('res.users', 'Rejected By', copy=False)
    approved_user_id = fields.Many2one('res.users', 'Approved By', copy=False)
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    remark = fields.Text('Remark')
    total = fields.Float('Total', digits=dp.get_precision('Product Price'), compute='_get_total_product_price')
    purchase_request_line_ids = fields.One2many('purchase.request.line', 'purchase_request_id', string="Products")
    stock_picking_ids = fields.One2many('stock.picking', 'purchase_request_id', string="Pickings")
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking count', default=0, store=True)

    @api.depends('stock_picking_ids')
    def _compute_picking_count(self):
        for order in self:
            order.picking_count = len(order.stock_picking_ids)

    @api.multi
    def action_view_picking(self):
        """ This function returns an action that display existing PR orders of given PR order ids. When only one found, show the PR immediately.
        """
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        result['context'] = {}
        picking_ids = self.mapped('stock_picking_ids')
        # choose the view_mode accordingly
        if not picking_ids or len(picking_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (picking_ids.ids)
        elif len(picking_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = picking_ids.id
        return result

    @api.multi
    def button_submit_for_approval(self):
        self.submission_date = datetime.now().date()
        self.eta_on_submission_date = self.submission_date + timedelta(days=self.pur_request_tmpl_id.vendor_lead_time or 0.0)
        if self.request_delivery_date <= self.eta_on_submission_date:
            raise ValidationError(
                "Request Delivery Date is (%s) which is less then or equal to ETA based on Submission Date (%s) !"%(
                self.request_delivery_date, self.eta_on_submission_date))
        self.state = 'pending_approval'

    @api.multi
    def button_approve(self):
        self.approval_date = datetime.now().date()
        self.eta_on_approval_date = self.approval_date + timedelta(days=self.pur_request_tmpl_id.vendor_lead_time or 0.0)
        if self.eta_on_approval_date > self.eta_on_approval_date:
            raise ValidationError(
                "ETA based on Approval date is (%s) which is greater then Request Delivery Date (%s) !" % (
                self.eta_on_approval_date, self.eta_on_approval_date))
        self.approved_user_id = self.env.user.id
        self.state = 'mgr_approve'

    @api.multi
    def button_reject(self):
        self.rejected_user_id = self.env.user.id
        self.state = 'request_reject'

    @api.multi
    def button_cancel(self):
        self.cancelled_user_id = self.env.user.id
        self.state = 'cancel'

    @api.multi
    def _get_total_product_price(self):
        for record in self:
            record.total = sum([x.total_order_price for x in record.purchase_request_line_ids])

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            outlet_code = ''
            if vals.get('outlet_id'):
                outlet_code = self.env['stock.warehouse'].browse(vals['outlet_id']).code
            vals['name'] = outlet_code + '/' + self.env['ir.sequence'].next_by_code('purchase.request.form') or _('New')
        return super(PurchaseRequest, self).create(vals)

    @api.onchange('requestor_id')
    def onchange_requestor_id(self):
        if self.requestor_id:
            outlets = self.env['stock.warehouse']
            if self.requestor_id.user_outlet_ids:
                outlets |= self.requestor_id.user_outlet_ids
            if self.requestor_id.manager_outlet_ids:
                outlets |= self.requestor_id.manager_outlet_ids
            if self.requestor_id.other_outlet_ids:
                outlets |= self.requestor_id.other_outlet_ids

            if outlets:
                self.outlet_id = outlets[0].id if len(outlets) == 1 else False
                return {'domain': {'outlet_id': [('id', 'in', [x.id for x in outlets]), ('is_outlet','=',True)]}}
            else:
                self.outlet_id = False
        else:
            self.outlet_id = False

    @api.onchange('partner_id','outlet_id')
    def onchange_partner_id(self):
        res = {'domain': {'pur_request_tmpl_id': [('id','=',-1)]}}
        if self.partner_id and self.outlet_id:
            today = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
            search_domain = [('partner_id','=',self.partner_id.id), ('start_date','<=',today), ('end_date','>=',today),('outlet_ids','child_of',[self.outlet_id.id])]
            request_tmpls = self.env['purchase.request.tmpl'].search(search_domain)
            res['domain']['pur_request_tmpl_id'] = search_domain
            if request_tmpls:
                self.pur_request_tmpl_id = request_tmpls[0].id if len(request_tmpls) == 1 else False
            else:
                self.pur_request_tmpl_id = False
        else:
            self.pur_request_tmpl_id = False
        return res

    @api.onchange('outlet_id')
    def onchange_outlet_id(self):
        if self.outlet_id:
            self.street = self.outlet_id.street
            self.street2 = self.outlet_id.street2
            self.zip = self.outlet_id.zip
            self.city = self.outlet_id.city
            self.state_id = self.outlet_id.state_id and self.outlet_id.state_id.id or False
            self.country_id = self.outlet_id.country_id and self.outlet_id.country_id.id or False

    @api.multi
    @api.constrains('request_delivery_date', 'state', 'pur_request_tmpl_id', 'submission_date')
    def check_request_delivery_date(self):
        for record in self:
            if record.request_delivery_date:
                create_date = datetime.strptime(record.create_date.strftime(DEFAULT_SERVER_DATE_FORMAT),DEFAULT_SERVER_DATE_FORMAT).date()

                if record.state == 'draft' and not (record.request_delivery_date >= create_date + timedelta(days=record.pur_request_tmpl_id.vendor_lead_time or 0.0)):
                    raise ValidationError('Request Delivery Date must be at least %s days from creation/submission date !'%record.pur_request_tmpl_id.vendor_lead_time)
                if record.submission_date and record.state == 'pending_approval' and not (record.request_delivery_date >= record.submission_date + timedelta(days=record.pur_request_tmpl_id.vendor_lead_time or 0.0)):
                    raise ValidationError('Request Delivery Date must be at least %s days from creation/submission date !' % record.pur_request_tmpl_id.vendor_lead_time)

    @api.multi
    def load_product_lines_from_template(self):
        if not self.pur_request_tmpl_id:
            raise ValidationError("Purcahse Request Template is missing !")
        request_line_obj = self.env['purchase.request.line']

        # unlink all line first to load lines again
        request_line_obj.search([('purchase_request_id','=',self.id)]).unlink()

        product_ids = []
        uom_obj = self.env['uom.uom']
        for req_tmpl_line in self.pur_request_tmpl_id.purchase_request_tmpl_line_ids.filter_tmpl_lines(self.outlet_id):
            for line_product in req_tmpl_line.product_ids:
                if line_product.id not in product_ids:
                    product_ids.append(line_product.id)

                    uom_po_id = line_product.uom_po_id
                    po_uom_ratio = line_product.uom_po_id.factor_inv
                    search_po_uom = uom_obj.with_context({'restrict_uom_on_product': line_product.id, 'type': 'purchase' }).search([], limit=1)
                    if search_po_uom:
                        uom_po_id = search_po_uom
                        multi_uom = self.env['product.multi.uom'].search([('product_tmpl_id','=',line_product.product_tmpl_id.id),
                                                              ('name','=',uom_po_id.id)], limit=1)
                        if multi_uom:
                            po_uom_ratio = multi_uom.factor_inv

                    request_line_obj.create({
                        'product_id':line_product.id,
                        'account_analytic_id' : self.outlet_id.analytic_account_id.id,
                        'on_hand_qty': self.env['purchase.request.line'].compute_on_hand_by_uom(line_product, self.outlet_id.lot_stock_id, uom_po_id),
                        'suggested_qty': 0.0,
                        'order_qty': 0.0,
                        'order_uom_id': uom_po_id.id,
                        'delivered_qty': 0.0,
                        'delivered_uom_id': uom_po_id.id,
                        'unit_price': line_product.outlet_standard_price,
                        'uom_id': line_product.uom_id.id,
                        'ratio': po_uom_ratio,
                        'total_order_price' : 0.0 * line_product.outlet_standard_price, # this should be order_qty -> convert to base uom qty * standard price
                        'purchase_request_id' : self.id
                    })

    @api.multi
    def create_po_from_pr(self):
        if len(list(set([x.partner_id.id for x in self]))) > 1:
            raise ValidationError('All PR must be of same Vendor !')
        if len(self) != len(self.filtered(lambda x: x.state == 'mgr_approve')):
            raise ValidationError('All PR Must be Approved by Manager !')
        if len(list(set([x.request_delivery_date for x in self]))) > 1:
            raise ValidationError('All PR must be of same Request Delivery Date !')
        product_uom_dict = {}
        for record in self:
            for line in record.purchase_request_line_ids:
                if line.product_id not in product_uom_dict.keys():
                    product_uom_dict[line.product_id] = [line.order_uom_id]
                else:
                    if line.order_uom_id not in product_uom_dict[line.product_id]:
                        product_uom_dict[line.product_id].append(line.order_uom_id)
        validation_message = []
        for product in product_uom_dict:
            if len(product_uom_dict[product]) > 1:

                validation_message.append("Product '%s' must have same UOM across all PR here it has different which are as following '%s'. \n"%(product.name,', '.join(x.name for x in product_uom_dict[product])))

        if validation_message:
            raise ValidationError(validation_message)
        # above part is all validation

        # bellow part start creating PO with consolidation of PR lines
        order_lines = {}
        for record in self:
            for line in record.purchase_request_line_ids.filtered(lambda x: x.order_qty):
                if line.product_id.id not in order_lines.keys():
                    order_lines[line.product_id.id] = {'product_id': line.product_id.id,
                                                       'name': line.product_id.display_name,
                                                       'product_qty': line.order_qty,
                                                       'price_unit' : 0.0,
                                                       'product_uom': line.order_uom_id.id,
                                                       'old_product_uom' : line.order_uom_id.id, # this field is for the conversion of quantity in PO line when change UOM
                                                       'date_planned': datetime.today(),
                                                       'account_analytic_id' : self[0].partner_id.property_account_payable_id.account_analytic_id.id
                                                       }
                else:
                    order_lines[line.product_id.id]['product_qty'] += line.order_qty

        if not order_lines:
            raise ValidationError("There is noting to create PO from PR ! \n make sure you key in the Order Qty for Request lines.")

        po_vals = {'partner_id':self[0].partner_id.id,
                   'order_line': [[0, False, order_lines[line]] for line in order_lines]}

        purchase_order = self.env['purchase.order'].create(po_vals)
        for po_line in purchase_order.order_line:
            po_line._compute_tax_id()
            po_line._onchange_quantity()
        if purchase_order:
            self.write({'purchase_order_id' : purchase_order.id,
                        'po_raise_user_id' :  self.env.user.id,
                        'state' : 'po_raised'
                        })


class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"

    product_id = fields.Many2one('product.product', string='Product')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True)
    on_hand_qty = fields.Float('OnHand Qty')
    suggested_qty = fields.Float('Suggested Qty')
    increase_or_reduce = fields.Selection([('increase','Increase'),('reduce','Reduce'),('same','Same')], string="Increase/Reduce")
    percentage = fields.Float('Percentage %')
    order_qty = fields.Float('Order Qty', digits=dp.get_precision('Product Unit of Measure'))
    order_uom_id = fields.Many2one('uom.uom', 'Order UOM')
    delivered_qty = fields.Float('Deliverd Qty', digits=dp.get_precision('Product Unit of Measure'))
    delivered_uom_id = fields.Many2one('uom.uom', 'Delivered UOM')
    unit_price = fields.Float('U/Price', digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', 'U/Price UOM')
    ratio = fields.Float('Ratio')
    total_order_price = fields.Float('Total Price', digits=dp.get_precision('Product Price'))
    purchase_request_id = fields.Many2one('purchase.request', string="Purcahse Request")

    @api.onchange('order_qty', 'order_uom_id', 'product_id')
    def onchange_order_qty_uom_ratio(self):
        if self.product_id and self.order_uom_id:
            self.on_hand_qty = self.compute_on_hand_by_uom(self.product_id,
                                                           self.purchase_request_id.outlet_id.lot_stock_id,
                                                           self.order_uom_id)
            multi_uom = self.env['product.multi.uom'].search(
                [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                 ('name', '=', self.order_uom_id.id)], limit=1)
            if multi_uom:
                self.ratio = multi_uom.factor_inv
            else:
                self.ratio = self.order_uom_id.factor_inv

        if self.order_qty and self.order_uom_id and self.ratio and self.product_id:
            base_uom_qty = self.order_uom_id.with_context({'product_tmpl_id':self.product_id.product_tmpl_id.id})._compute_quantity(self.order_qty, self.product_id.uom_id, rounding_method='HALF-UP')
            self.total_order_price = base_uom_qty * self.product_id.outlet_standard_price
        else:
            self.total_order_price = 0.0

    def compute_on_hand_by_uom(self, product_id, location_id, by_uom_id):
        product_on_hand = product_id.with_context(
            {'location': location_id.id})._compute_quantities_dict(None, None, None)
        return product_id.uom_id.with_context({'product_tmpl_id': product_id.product_tmpl_id.id}
                                              )._compute_quantity(product_on_hand[product_id.id]['qty_available'],
                                                                  by_uom_id, rounding_method='HALF-UP')








