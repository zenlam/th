# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    deny_outlet_ids = fields.One2many(comodel_name='outlet.ordering.product.deny', inverse_name='product_id')


class ProductMultiUom(models.Model):
    _inherit = 'product.multi.uom'

    barcode = fields.Char(string=_('HAVI Code'))
