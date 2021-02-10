# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_asset = fields.Boolean(string=_('is Asset'), default=False)
    asset_category_id = fields.Many2one(
        comodel_name='account.asset.category.custom',
        string=_('Asset Category'))

    @api.onchange('is_asset')
    def onchange_is_asset(self):
        """
        auto remove asset category if product is not asset
        :return:
        """
        if not self.is_asset:
            self.asset_category_id = False
        else:
            self.type = 'consu'

    @api.constrains('is_asset', 'type')
    def _asset_product_type_constrains(self):
        for prod in self:
            if prod.is_asset and not prod.type == 'consu':
                raise Warning(_('Product Type has to be consumable for '
                                'asset product.'))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('is_asset')
    def onchange_is_asset(self):
        if self.is_asset:
            self.type = 'consu'

    @api.constrains('is_asset', 'type')
    def _asset_product_type_constrains(self):
        for prod in self:
            if prod.is_asset and not prod.type == 'consu':
                raise Warning(_('Product Type has to be consumable for '
                                'asset product.'))
