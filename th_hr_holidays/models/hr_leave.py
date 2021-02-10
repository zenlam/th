from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _get_number_of_days(self, date_from, date_to, employee_id):
        res = super(HrLeave, self)._get_number_of_days(date_from, date_to, employee_id)
        ph_data = self.env['hr.holidays'].with_context(raise_wn=False).get_days_match(date_from, date_to, employee_id=employee_id)
        return res - ph_data


HrLeave()
