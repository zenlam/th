# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    is_asset = fields.Boolean(string=_('Is Asset?'),
                              related='product_id.is_asset')
    removal_date = fields.Date(string='Expiry Date', required=False)

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id.id:
            if self.product_id.is_asset:
                self.life_date = False
                self.alert_date = False
                self.removal_date = False
                self.use_date = False
        return
