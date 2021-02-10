from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    cap_days = fields.Integer('Cap Days')
    carry_expired_date = fields.Date('Carry Forward Expire by', required=True)

    @api.constrains('cap_days')
    def check_cap_days(self):
        if self.cap_days < 0:
            raise UserError(_("Cap Days can't be Negative."))
