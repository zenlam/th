# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from openerp.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.depends('config_id', 'statement_ids', 'config_id.cash_control',
                 'statement_ids.journal_id', 'statement_ids.journal_id.type',
                 'statement_ids.journal_id.is_rounding_method')
    def _compute_cash_all(self):
        """ Will rewrite the whole function due to the old base logic is no
        longer applicable.
        """
        for session in self:
            session.cash_journal_id = False
            session.cash_control = False
            session.cash_register_id = False
            session.rounding_cash_register_id = False
            if session.config_id.cash_control:
                for statement in session.statement_ids:
                    if statement.journal_id.type == 'cash':
                        if statement.journal_id.is_rounding_method:
                            session.rounding_cash_register_id = statement.id
                        else:
                            session.cash_control = True
                            session.cash_journal_id = statement.journal_id.id
                            session.cash_register_id = statement.id
                if not session.cash_control and session.state != 'closed':
                    raise UserError(_(
                        "Cash control can only be applied to cash journals."))

    rounding_cash_register_id = fields.Many2one(
        'account.bank.statement',
        compute='_compute_cash_all',
        string='Rounding Cash Register',
        store=True)

    @api.model
    def create(self, vals):
        """
        Inherit the create function to change the balance start of rounding
        statement
        """
        res = super(PosSession, self).create(vals)
        if res.rounding_cash_register_id:
            res.rounding_cash_register_id.balance_start = 0
        return res
