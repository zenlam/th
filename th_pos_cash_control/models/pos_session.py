# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosSession(models.Model):
    _inherit = 'pos.session'

    in_out_logs = fields.One2many('cash.in.out.log', 'session_id',
                                  string='Cash In Out Logs')
    # create information fields to show the actual closing and difference
    cash_register_balance_end_actual = fields.Monetary(
        string='Actual Closing Balance',
        default=0)
    cash_register_difference_actual = fields.Monetary(
        string='Actual Difference',
        compute='_get_difference_actual')

    def _get_difference_actual(self):
        """
        Get the difference between the actual closing balance and theoretical
        closing balance.
        """
        for session in self:
            session.cash_register_difference_actual = \
                session.cash_register_balance_end_actual - \
                session.cash_register_balance_end

    @api.multi
    def view_cash_in_out(self):
        """
        Action to view a new window of cash in out log. Triggered from Cash
        Drawer Open History button.
        """
        self.ensure_one()
        return {
            'name': _('Cash Drawer Open History'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref(
                'th_pos_cash_control.th_view_cash_in_out_log_tree_view').id,
            'res_model': 'cash.in.out.log',
            'target': 'new',
            'domain': [('session_id', '=', self.id)]
        }

    @api.multi
    def _check_pos_session_balance(self):
        """
        Always post the theoretical closing balance for the session.
        :return:
        """
        super(PosSession, self)._check_pos_session_balance()
        for session in self:
            cash_statement = session.cash_register_id
            if session.config_id.cash_control and cash_statement:
                cash_statement.write({
                    'balance_end_real':
                        cash_statement.balance_start +
                        cash_statement.total_entry_encoding
                })

    @api.multi
    def action_pos_session_validate(self):
        """
        Always post the theoretical closing balance as real closing balance,
        hence need to prompt message when there is a difference between
        the theoretical closing balance and the actual closing balance
        (input from user).
        """
        confirm = self.env.context.get('confirm', False)
        if not confirm and \
                self.cash_register_balance_end_actual != \
                self.cash_register_balance_end:
            return {
                'name': 'Close POS Session Confirmation',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.session.closing.confirm',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'session_id': self.id},
            }
        else:
            super(PosSession, self).action_pos_session_validate()

    @api.model
    def create(self, vals):
        """
        Inherit the create function to change the balance start of cash
        statement
        """
        res = super(PosSession, self).create(vals)
        if res.cash_register_id:
            res.cash_register_id.balance_start = \
                res.config_id.default_opening_balance
        return res
