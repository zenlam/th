# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountAssetAssetCustom(models.Model):
    _inherit = "account.asset.asset.custom"
    
    @api.multi
    def open_asset_disposal_entries(self):
        for asset in self:
            return {
                'name': _('Disposal Entries'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', '=', asset.asset_move_id.id)],
            }
    
    # @api.multi
    # def open_material_requisitions(self):
    #     maintenance_list = []
    #     for asset in self:
    #         maintenance_list = self.env['maintenance.request'].search([('custom_asset_id','=',asset.id)])
    #         material_requisiton = self.env['material.purchase.requisition'].search([('maintenance_id','in',maintenance_list.ids)])
    #         return {
    #             'name': _('Material Requisitions'),
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             'res_model': 'material.purchase.requisition',
    #             'view_id': False,
    #             'type': 'ir.actions.act_window',
    #             'domain': [('id', 'in', material_requisiton.ids)],
    #         }
        
    @api.multi
    def open_asset_invoice(self):
        for asset in self:
            return {
                'name': _('Invoice'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', '=', asset.disposal_invoice_id.id)],
            }
    
    @api.multi
    def open_asset_depreciations(self):
        for asset in self:
            asset_lists = self.env['account.asset.depreciation.line.custom'].search([('asset_id', '=', asset.id)])
            return {
                'name': _('Account Asset Depreciation Line'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.asset.depreciation.line.custom',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', asset_lists.ids)],
            }
        