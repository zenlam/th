from odoo import api, fields, models, _


class HrJob(models.Model):
    _inherit = 'hr.job'

    leave_entitled_ids = fields.One2many('hr.leave.entitled', 'position_id',
                                         string="Leave Entitled")
