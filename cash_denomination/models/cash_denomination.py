# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CashDenomination(models.Model):
    """
    This model is used as master data of cash denomination
    """
    _name = 'cash.denomination'
    _description = 'Cash Denomination'
    _order = 'number desc'

    name = fields.Char(string='Name', required=1)
    number = fields.Float(string='Number', required=1)
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 required=1,
                                 default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('name_uniq', 'unique (name, company_id)',
         'The cash denomination name must be unique !'),
        ('number_uniq', 'unique (number, company_id)',
         'The cash denomination number must be unique !')
    ]