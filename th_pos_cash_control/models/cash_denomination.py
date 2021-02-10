# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CashDenomination(models.Model):
    _inherit = 'cash.denomination'

    @api.model
    def create(self, vals):
        """
        When the user creates a new cash denomination, then add the new
        denomination to every outlet.
        """
        res = super(CashDenomination, self).create(vals)
        outlets = self.env['stock.warehouse'].search(
            [('create_from', '=', 'outlet')])
        for outlet in outlets:
            outlet.default_cash_denominations = [(4, res.id)]
        return res
