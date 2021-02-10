from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    xid_mapping = fields.Integer(string="XId Mapping")

    _sql_constraints = [
        ('unique_xid_mapping', 'unique (xid_mapping)', 'XId mapping already exists!')
    ]


HrEmployee()
