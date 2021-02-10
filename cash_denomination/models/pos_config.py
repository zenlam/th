# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_cash_denominations = fields.Many2many(
        'cash.denomination',
        'config_cash_denomination_rel',
        'config_id',
        'denomination_id',
        string='Default Cash Denomination')

    @api.onchange('cash_control')
    def onchange_cash_control(self):
        """
        If the cash control boolean field is ticked, then auto load all cash
        denominations. Remove the cash denominations when it is unticked.
        """
        if self.cash_control:
            cash_denominations = self.env['cash.denomination'].search([])
            if cash_denominations:
                self.default_cash_denominations = \
                    [(6, 0, cash_denominations.ids)]
        else:
            self.default_cash_denominations = False


class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    @api.model
    def default_get(self, fields):
        """
        Load the config cash denominations into the Set Opening Balance and
        Set Closing Balance wizard view instead of the default_cashbox_lines.
        """
        vals = super(AccountBankStmtCashWizard, self).default_get(fields)
        config_id = self.env.context.get('default_pos_id')
        if config_id and self.env.user.has_group(
                'cash_denomination.group_cash_denomination'):
            config = self.env['pos.config'].browse(config_id)
            denominations = config.default_cash_denominations
            if denominations:
                vals['cashbox_lines_ids'] = [
                    [0, 0, {'coin_value': denomination.number, 'number': 0,
                            'subtotal': 0}] for denomination in denominations]
        return vals
