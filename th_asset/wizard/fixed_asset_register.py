from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FixedAssetRegister(models.TransientModel):
    _name = "fixed.asset.register"

    start_date = fields.Date(string="Asset Start Date", required=True)
    end_date = fields.Date(string="Asset End Date", required=True)

    @api.one
    @api.constrains('start_date', 'end_date')
    def check_start_date_end_date(self):
        if self.end_date < self.start_date:
            raise ValidationError(
                _('Start date must be smaller then end date !'))

    @api.multi
    def export_fixed_asset_register(self):
        report_name = 'fixed_asset_register'
        report = {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': report_name,
            'context': dict(self.env.context),
            'data': {'dynamic_report': True},
        }
        return report
