from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    region_id = fields.Many2one(string="Region", comodel_name="res.country.area")


HrEmployee()
