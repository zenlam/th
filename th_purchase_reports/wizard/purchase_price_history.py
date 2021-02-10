from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchasePriceHistory(models.TransientModel):
    _name = "purchase.price.history"

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    partner_ids = fields.Many2many('res.partner', string="Vendor")
    product_ids = fields.Many2many('product.template', string="Product")

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


    @api.multi
    def action_print(self):
        report_name = 'purchase_price_history'
        report = {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': report_name,
            'context': dict(self.env.context),
            'data': {'dynamic_report': True},
        }
        return report
