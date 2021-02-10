# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Location(models.Model):
    _inherit = "stock.location"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')