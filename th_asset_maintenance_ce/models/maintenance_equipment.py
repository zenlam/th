# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    @api.model
    def _cron_generate_requests(self):
        """
            Generates maintenance request on the next_action_date or today if none exists
        """
        res = super(MaintenanceEquipment, self)._cron_generate_requests()
        print('res================================',res)
        maintenance = self.env['maintenance.request'].search([('custom_asset_id', '!=', False),
                                                    ('maintenance_type', '=', 'preventive'),
                                                ('custom_frequency_next_date', '=', fields.Date.today())])
        print('maintenance===================',maintenance)
        for line in maintenance:
            if line:
                new_line = line.copy()
                new_line.write({'custom_frequency_start_date': fields.Date.today(), 'custom_previous_maintenance_id': line.id})
                print('new_line============================',new_line)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
