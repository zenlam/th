from odoo import fields, models, api


class ActionView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=[('staff', 'Staff')])


ActionView()
