# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Asset(models.Model):
    _inherit = 'account.asset.asset.custom'

    @api.multi
    def show_next_maintenance(self):
        self.ensure_one()
        res = self.env.ref('maintenance.hr_equipment_request_action')
        res = res.read()[0]
        res['domain'] = str([('custom_asset_id', '=', self.id)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
