# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category.custom'
    
    asset_maintenance_team_id = fields.Many2one(
        'maintenance.team',
        string="Maintenance Team",
    )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
