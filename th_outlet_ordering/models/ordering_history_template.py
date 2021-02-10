# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models,fields, api, _


class OutletOrderingHistoricalCalculation(models.Model):
    _inherit = 'purchase.requisition.template'
    _name = 'outlet.ordering.history.template'

    date_type = fields.Selection(selection=[('specific_date', _('Specific Date')),
                                            ('request_date', _('Stock Request Date'))],
                                 string='Date Based on', required=True)
    _sql_constraints = [
        ('code_uniq', 'unique(code)', "Outlet Ordering History Template Code Already Exist !"),
    ]
