# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    default = fields.Boolean(string=_('Is Default Supplier?'), default=False,
                             help=_('Enable this check box consider this Supplier Is Default Supplier.'))
