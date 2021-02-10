from odoo import fields, models, api


class EmployeeType(models.Model):
    _name = "planning.role"

    name = fields.Char(string="Employee Position", required=True)
    colour = fields.Char(string="Colour", default="green")

    @api.model
    def get_form_view_id(self, access_uid=None):
        return self.env.ref('t_staff_planning.staff_planning_role_form_view').id


EmployeeType()
