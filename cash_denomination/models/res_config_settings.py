# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    """
    Allow the user to choose to enable or disable cash denomination feature
    """
    _inherit = 'res.config.settings'

    group_cash_denomination = fields.Boolean(
        string='Enable Cash Denominations',
        help='Allow system to manage the opening and closing balance using '
             'predefined cash denominations.',
        implied_group='cash_denomination.group_cash_denomination')

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        group_cash_denomination = self.group_cash_denomination or False
        param.set_param(
            'cash_denomination.cash_denomination', group_cash_denomination)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            group_cash_denomination=self.env[
                'ir.config_parameter'].sudo().get_param(
                'cash_denomination.cash_denomination')
        )
        return res
