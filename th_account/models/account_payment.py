# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=1)

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        """ Returns values common to both move lines
        Note: This function will create accounting entry when validating a payment
        """
        res = super(AccountPayment, self)._get_shared_move_line_vals(debit, credit, amount_currency, move_id, invoice_id)
        res.update({
            'analytic_account_id': self.analytic_account_id.id,
        })
        return res


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=1)

    @api.multi
    def _prepare_payment_vals(self, invoices):
        """ Create the payment values.
        Note: This function will create a payment when the user selects multiple invoice to register payment and use
        the analytic account in the wizard as the analytic account.
        """
        res = super(AccountRegisterPayments, self)._prepare_payment_vals(invoices)
        res.update({
            'analytic_account_id': self.analytic_account_id.id,
        })
        return res

