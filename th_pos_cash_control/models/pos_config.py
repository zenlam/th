# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_opening_balance = fields.Float(string=_('Default Opening Balance'),
                                           help='Used to populate the opening '
                                                'balance for every new pos '
                                                'session under this config.')
    default_cash_denominations = fields.Many2many(
        'cash.denomination',
        'config_cash_denomination_rel',
        'config_id',
        'denomination_id',
        string='Default Cash Denomination')

    @api.onchange('outlet_id')
    def onchange_outlet_id(self):
        """
        Change the value of cash control of config based on the outlet.
        Populate the payment methods of config based on the outlet.
        Change the value of stock location of config based on the outlet.
        Change the value of opening balance of config based on the outlet.
        Populate the cash denominations of config based on the outlet.
        """
        if self.outlet_id:
            self.cash_control = self.outlet_id.cash_control
            self.journal_ids = self.outlet_id.default_payment_methods.ids
            self.stock_location_id = self.outlet_id.lot_stock_id.id
            if self.cash_control:
                self.default_opening_balance = \
                    self.outlet_id.default_opening_balance
                cash_denominations = self.outlet_id.default_cash_denominations
                if cash_denominations:
                    self.default_cash_denominations = \
                        [(6, 0, cash_denominations.ids)]
                else:
                    self.default_cash_denominations = False
        else:
            self.cash_control = False
            self.default_opening_balance = 0
            self.journal_ids = False
            self.stock_location_id = False
            self.default_cash_denominations = False

    @api.onchange('cash_control')
    def onchange_cash_control(self):
        """
        If the user untick the cash control, set opening balance to 0 and
        empty the cash denominations.
        """
        if not self.cash_control:
            self.default_opening_balance = 0
            self.default_cash_denominations = False


class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    @api.multi
    def validate(self):
        """
        Due to the closing balance posting of a session always follows the
        theoretical closing balance, hence need to pass the actual closing
        balance from Set Closing Balance wizard to the session for reporting
        purpose.
        """
        res = super(AccountBankStmtCashWizard, self).validate()
        bnk_stmt_id = self.env.context.get('bank_statement_id', False) or \
            self.env.context.get('active_id', False)
        bnk_stmt = self.env['account.bank.statement'].browse(bnk_stmt_id)
        total = 0.0
        for lines in self.cashbox_lines_ids:
            total += lines.subtotal
        if self.env.context.get('balance', False) == 'end':
            # closing balance
            bnk_stmt.pos_session_id.write({
                'cash_register_balance_end_actual': total
            })
        return res
