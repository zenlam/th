from odoo import fields, models, api


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection([('tree', 'Tree'),
                             ('form', 'Form'),
                             ('graph', 'Graph'),
                             ('pivot', 'Pivot'),
                             ('calendar', 'Calendar'),
                             ('diagram', 'Diagram'),
                             ('gantt', 'Gantt'),
                             ('kanban', 'Kanban'),
                             ('staff', 'staff'),
                             ('search', 'Search'),
                             ('qweb', 'QWeb')], string='View Type')


View()
