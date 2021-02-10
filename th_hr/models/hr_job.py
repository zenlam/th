from odoo import api, fields, models, _


class HrJob(models.Model):
    _inherit = "hr.job"

    default_labour_cost = fields.Float(string="Default Labor Cost")
    working_time_rule_id = fields.Many2one(comodel_name='working.time.rules', string="Working Time Rule", required=True)
    employee_type = fields.Selection([('full_timer', 'Full timer'),
                                      ('part_timer', 'Part timer'),
                                      ('hq_staff', 'HQ Staff'),
                                      ('casual_labor', 'Casual Labor'),
                                      ('other', 'Other')], string="Employee Type", required=True)


HrJob()
