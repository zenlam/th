# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.point_of_sale.wizard.pos_box import PosBox
from datetime import datetime


class PosBoxIn(PosBox):
    """
    Add Cash Control to Put Money In model
    """
    _inherit = 'cash.box.in'

    cash_control_id = fields.Many2one('cash.control', string='Cash Control',
                                      required=1,
                                      domain=[('action', 'in',
                                               ('put_in', 'failed_bank_in'))])

    @api.multi
    def _calculate_values_for_statement_line(self, record):
        """
        Post the Put Money In Accounting Entry based on the cash control.
        Generate log for the transaction.
        """
        values = super(PosBoxIn, self)._calculate_values_for_statement_line(
            record)
        if self.cash_control_id and \
                self.cash_control_id.debit_account_id and \
                self.cash_control_id.credit_account_id:
            values.update(
                account_id=self.cash_control_id.credit_account_id.id,
                reconcile_account_id=self.cash_control_id.debit_account_id.id,
                name='{0}: {1}'.format(self.cash_control_id.name, self.name),
            )

            # create cash in log
            in_log_value = self._prepare_cash_in_log_values()
            self.env['cash.in.out.log'].create(in_log_value)
        return values

    def _prepare_cash_in_log_values(self):
        """
        Return dictionary of creating the cash in log
        """
        context = self.env.context or {}
        return {
            'user_id': self.env.user.id,
            'reason': '{0}: {1}'.format(self.cash_control_id.name, self.name),
            'session_id': context.get('active_id'),
            'date': datetime.now(),
            'action': 'in',
            'amount': self.amount or 0.0,
        }


class PosBoxOut(PosBox):
    """
    Add Cash Control to Take Money Out model
    """
    _inherit = 'cash.box.out'

    cash_control_id = fields.Many2one('cash.control', string='Cash Control',
                                      required=1,
                                      domain=[('action', 'in',
                                               ('take_out', 'bank_in'))])

    @api.multi
    def _calculate_values_for_statement_line(self, record):
        """
        Post the Take Money Out Accounting Entry based on the cash control.
        Generate log for the transaction.
        """
        values = super(PosBoxOut, self)._calculate_values_for_statement_line(
            record)
        if self.cash_control_id and \
                self.cash_control_id.debit_account_id and \
                self.cash_control_id.credit_account_id:
            values.update(
                account_id=self.cash_control_id.debit_account_id.id,
                reconcile_account_id=self.cash_control_id.credit_account_id.id,
                name='{0}: {1}'.format(self.cash_control_id.name, self.name),
            )
            # create cash out log
            out_log_value = self._prepare_cash_out_log_values()
            self.env['cash.in.out.log'].create(out_log_value)
        return values

    def _prepare_cash_out_log_values(self):
        """
        Return dictionary of creating the cash out log
        """
        context = self.env.context or {}
        return {
            'user_id': self.env.user.id,
            'reason': '{0}: {1}'.format(self.cash_control_id.name, self.name),
            'session_id': context.get('active_id'),
            'date': datetime.now(),
            'action': 'out',
            'amount': self.amount or 0.0,
        }
