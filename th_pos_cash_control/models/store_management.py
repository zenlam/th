# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class OutletManagement(models.Model):
    _inherit = 'stock.warehouse'

    def _get_default_cash_denominations(self):
        """
        Always populate all cash denominations by default
        """
        return self.env['cash.denomination'].search([]).ids

    def _get_default_payment_methods(self):
        """
        Always populate the account journals (meet specific conditions) as
        payment method by default.
        """
        return self.env['account.journal'].search(
            [('journal_user', '=', 1), ('type', 'in', ('bank', 'cash'))]).ids

    # cash control
    cash_control = fields.Boolean(string=_('Cash Control'), default=True)
    default_opening_balance = fields.Float(string=_('Default Opening Balance'),
                                           default=0,
                                           help='Used to populate the opening '
                                                'balance for every new pos '
                                                'config under this outlet.')
    default_cash_denominations = fields.Many2many(
        'cash.denomination',
        'outlet_cash_denomination_rel',
        'outlet_id',
        'denomination_id',
        string='Default Cash Denomination',
        default=_get_default_cash_denominations)
    default_payment_methods = fields.Many2many(
        'account.journal',
        'outlet_payment_method_rel',
        'outlet_id', 'method_id',
        string='Default Payment Method',
        default=_get_default_payment_methods,
        domain=[('journal_user', '=', 1), ('type', 'in', ('bank', 'cash'))])

    @api.onchange('cash_control')
    def onchange_cash_control(self):
        """
        Always populate the default value of cash denominations and payment
        method when the cash control field is ticked.
        """
        if self.cash_control:
            self.default_cash_denominations = \
                self._get_default_cash_denominations()
            self.default_payment_methods = self._get_default_payment_methods()
        else:
            self.default_cash_denominations = False
            self.default_payment_methods = False
