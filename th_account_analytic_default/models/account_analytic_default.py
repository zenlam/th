# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAnalyticDefault(models.Model):
    _inherit = "account.analytic.default"

    analytic_id = fields.Many2one(required=True)
