# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PosSessionClosingConfirm(models.TransientModel):
    """
    This wizard will be used when the theoretical closing balance is different
    from the actual closing balance (input from pos user) in POS session.
    """
    _name = 'pos.session.closing.confirm'
    _description = 'POS Session Closing Confirmation'

    @api.multi
    def action_confirm(self):
        """
        Run action_pos_session_validate if the user would like to proceed when
        there is a difference between the actual closing balance and the
        theoretical closing balance.
        """
        self.ensure_one()
        session = self.env['pos.session'].browse(
            self.env.context.get('session_id', False))
        session.with_context(confirm=True).action_pos_session_validate()
