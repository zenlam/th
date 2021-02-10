# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=1)

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        """ Return the first move line dict for voucher entry posting
        Note: This function will return the move line values to the previous function to create voucher entry when
        the user validate a voucher.
        """
        res = super(AccountVoucher, self).first_move_line_get(move_id, company_currency, current_currency)
        res.update({
            'analytic_account_id': self.account_analytic_id.id,
        })
        return res


class AccountVoucherLine(models.Model):
    _inherit = "account.voucher.line"

    account_analytic_id = fields.Many2one(required=1)
