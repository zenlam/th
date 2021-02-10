# --*-- coding: utf-8 --*--
from openerp import fields, models, api, _


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    reconcile_account_id = fields.Many2one(
        'account.account',
        string='Reconcile Account',
        help='Reconcile account value is passed from cash control to perform '
             'reconciliation of the take money out or put money in actions.')

    def _prepare_reconciliation_move_line(self, move, amount):
        """ This function creates the reconciliation line for bank statement
        move line. If the bank statement line is related to take money out or
        put money in actions, then the bank statement line will have value in
        reconcile_account_id (from cash control). Hence, the posting should use
        the reconcile_account_id instead of debit_account_id or
        credit_account_id of the cash journal.
        """
        values = super(AccountBankStatementLine, self)\
            ._prepare_reconciliation_move_line(move, amount)
        if self.reconcile_account_id:
            values.update(account_id=self.reconcile_account_id.id)
        return values
