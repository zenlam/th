# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, api, models, _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_asset = fields.Boolean(related='lot_id.product_id.is_asset',
                              string=_('Is Asset'))
