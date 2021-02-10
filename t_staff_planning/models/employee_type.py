from odoo import fields, models, api


class EmployeeType(models.Model):
    _name = "employee.type"

    employee_type = fields.Char(string="Employee Type", required=True)
    employee_type_code = fields.Char(string="Employee Code", required=True)


EmployeeType()
