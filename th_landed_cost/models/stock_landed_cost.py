# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    purchase_order_id = fields.Many2one(comodel_name="purchase.order",
                                        string="Purchase Order")

    @api.multi
    def action_view_journal_item(self):
        self.ensure_one()
        action = self.env.ref(
            'account.action_account_moves_all_a').read()[0]
        action['domain'] = [('move_id', '=', self.account_move_id.id)]
        return action


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    def _create_account_move_line(self, move, credit_account_id,
                                  debit_account_id, qty_out,
                                  already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = []
        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
            'analytic_account_id': self.move_id.account_analytic_id.id,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.append([0, 0, debit_line])
        AccountMoveLine.append([0, 0, credit_line])

        # Create account move lines for quants already out of stock
        if qty_out > 0:
            debit_line = dict(base_line,
                              name=(self.name + ": " + str(qty_out) + _(
                                  ' already out')),
                              quantity=0,
                              account_id=already_out_account_id)
            credit_line = dict(base_line,
                               name=(self.name + ": " + str(qty_out) + _(
                                   ' already out')),
                               quantity=0,
                               account_id=debit_account_id)
            diff = diff * qty_out / self.quantity
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            AccountMoveLine.append([0, 0, debit_line])
            AccountMoveLine.append([0, 0, credit_line])

            # TDE FIXME: oh dear
            if self.env.user.company_id.anglo_saxon_accounting:
                debit_line = dict(base_line,
                                  name=(self.name + ": " + str(qty_out) + _(
                                      ' already out')),
                                  quantity=0,
                                  account_id=credit_account_id)
                credit_line = dict(base_line,
                                   name=(self.name + ": " + str(qty_out) + _(
                                       ' already out')),
                                   quantity=0,
                                   account_id=already_out_account_id)

                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                AccountMoveLine.append([0, 0, debit_line])
                AccountMoveLine.append([0, 0, credit_line])
        return AccountMoveLine