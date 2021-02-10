from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PONotFullyInvoiced(models.TransientModel):
    _name = "po.not.fully.invoiced"

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    partner_ids = fields.Many2many('res.partner', string="Vendor")
    product_ids = fields.Many2many('product.template', string="Product")
    product_categ_ids = fields.Many2many('product.category',
                                         string="Product Category")
    type_stockable = fields.Boolean('Stockable', default=True)
    type_consumable = fields.Boolean('Consumbale')
    type_service = fields.Boolean('Service')
    invoice_type = fields.Selection(
        [('partial', 'Partially Invoiced'), ('not', 'Not Invoiced')],
        'Invoice Type', default='partial', required=True)
    report_type = fields.Selection(
        [('summary', 'Summary'), ('detail', 'Detailed')], 'Report Type',
        default='summary', required=True)

    @api.constrains('start_date', 'end_date')
    def check_start_date_end_date(self):
        if self.end_date < self.start_date:
            raise UserError(_('Start date must be smaller than end date !'))

    @api.constrains('partner_ids', 'product_ids')
    def check_partner_product(self):
        if not (self.partner_ids or self.product_ids):
            raise UserError(_("Both 'Product' and 'Vendor' can't be empty "
                              "at the same time!\n"
                              "Please fill either one field or both."))

    @api.onchange('product_categ_ids', 'type_stockable', 'type_consumable',
                  'type_service')
    def onchange_product_categ_ids(self):
        product_domain = []

        if self.type_stockable:
            if product_domain:
                product_domain.insert(0, '|')
                product_domain += [('type', '=', 'product')]
            else:
                product_domain += [('type', '=', 'product')]

        if self.type_consumable:
            if product_domain:
                product_domain.insert(0, '|')
                product_domain += [('type', '=', 'consu')]
            else:
                product_domain += [('type', '=', 'consu')]

        if self.type_service:
            if product_domain:
                product_domain.insert(0, '|')
                product_domain += [('type', '=', 'service')]
            else:
                product_domain += [('type', '=', 'service')]

        if self.product_categ_ids:
            if product_domain:
                product_domain.insert(0, ('categ_id', 'child_of',
                                          [x.id for x in
                                           self.product_categ_ids]))
                product_domain.insert(0, '&')
            else:
                product_domain += [('categ_id', 'child_of',
                                    [x.id for x in self.product_categ_ids])]
        return {'domain': {'product_ids': product_domain}}

    @api.multi
    def action_print(self):
        report_name = 'po_not_fully_invoiced'
        report = {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': report_name,
            'context': dict(self.env.context),
            'data': {'dynamic_report': True},
        }
        return report
