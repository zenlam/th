# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CashInOutLog(models.Model):
    """
    This model is used to keep track the transaction of Put Money In and Take
    Money Out in the POS session.
    """
    _name = 'cash.in.out.log'
    _order = 'date asc'

    user_id = fields.Many2one('res.users', string='User')
    reason = fields.Char(string='Reason')
    session_id = fields.Many2one('pos.session', string='Session')
    date = fields.Datetime(string='Date')
    action = fields.Selection(selection=[('in', 'In'), ('out', 'Out')],
                              string='Action')
    amount = fields.Float(string='Amount', default=0)
