# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    outlet_standard_price = fields.Float(
        string=_('Outlet Standard Cost'), digits=dp.get_precision('Product Price'),
        help=_('Standard Outlet Cost of the product, in the default UOM of the product.'),
        required=True,
        default=0.0,
        track_visibility='onchange',
    )
