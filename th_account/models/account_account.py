# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True)
