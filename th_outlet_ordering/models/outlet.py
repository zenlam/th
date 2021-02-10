# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Outlet(models.Model):
    _inherit = 'stock.warehouse'

    deny_product_ids = fields.One2many(comodel_name='outlet.ordering.product.deny', inverse_name='outlet_id')
