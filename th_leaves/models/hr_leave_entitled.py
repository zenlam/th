from odoo import api, fields, models, _


class HrLeaveEntitled(models.Model):
    _name = "hr.leave.entitled"
    _order = 'service_year'

    position_id = fields.Many2one('hr.job', 'Employee Position')
    service_year = fields.Integer('Service Year')
    day_entitled = fields.Integer('Leave Entitled')
