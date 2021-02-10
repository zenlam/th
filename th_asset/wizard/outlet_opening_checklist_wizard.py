from odoo import models, fields, api, _


class OutletOpeningChecklistWizard(models.TransientModel):
    _name = 'opening.checklist.wizard'

    all_location = fields.Boolean(string='All Location')
    loc_ids = fields.Many2many('stock.location',
                               'stock_checklist_location_rel',
                               'col1',
                               'col2',
                               string='Choose Location')
    report_type = fields.Selection(
        selection=[
            ('location', 'By Location'),
            ('total', 'By Total'),
        ],
        string="Report Type",
    )

    @api.multi
    def print_outlet_opening_checklist_report(self):
        report_name = 'opening_checklist_wizard'
        ctx = self.env.context.copy()
        ctx.update({'all_location': self.all_location,
                    'location_ids': self.loc_ids.ids,
                    'report_type': self.report_type})
        report = {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': report_name,
            'context': ctx,
            'data': {'dynamic_report': True},
        }
        return report

    # Clear loc_ids field when all_location field is selected
    @api.onchange('all_location')
    def empty_loc_ids(self):
        self.loc_ids = [(6, 0, [])]
