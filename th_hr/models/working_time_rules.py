from odoo import fields, models, api


class WorkingTimeRules(models.Model):
    _name = "working.time.rules"

    _sql_constraints = [
        ('unique_name', 'unique (name)', 'Name already exists!')
    ]

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one(string="Company", comodel_name="res.company",
                                 default=lambda self: self.env.user.company_id)
    label_in_hours = fields.Char(string=" ", default="in Hours", readonly=1)
    sd_working_t = fields.Float(string="Standard Working Time (per day)")
    sd_break_time = fields.Float(string="Standard Break Time (per day)")
    ot_break_time = fields.Float(string="OT Break Time")
    max_ot = fields.Float(string="Maximum OT Time (per day)")
    ph_working_time = fields.Float(string="Public Holiday Working Time (per day)")


WorkingTimeRules()
