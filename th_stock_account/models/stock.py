# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id):
        """ Create the move line from the stock move.
        Note: This function will return move line values dict to the previous function when the user validate a picking.
        """
        res = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                    debit_account_id, credit_account_id)
        if res.get('credit_line_vals'):
            if self._is_internal():
                res['credit_line_vals'].update({
                    'analytic_account_id':
                        self.picking_id.location_id.account_analytic_id.id
                })
            else:
                res['credit_line_vals'].update({
                    'analytic_account_id': self.account_analytic_id.id,
                })
        if res.get('debit_line_vals'):
            if self._is_internal():
                res['debit_line_vals'].update({
                    'analytic_account_id':
                        self.picking_id.location_dest_id.account_analytic_id.id
                })
            else:
                res['debit_line_vals'].update({
                    'analytic_account_id': self.account_analytic_id.id,
                })
        if res.get('price_diff_line_vals'):
            res['price_diff_line_vals'].update({
                'analytic_account_id': self.account_analytic_id.id,
            })
        return res
