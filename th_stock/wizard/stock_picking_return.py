# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_move_default_values(self, return_line, new_picking):
        """ This function will return the dictionary of stock move values to _create_returns function.
        Note: Need to override this function to pass account analytic id to return move
        """
        res = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        res.update({
            'account_analytic_id': return_line.move_id.account_analytic_id.id,
        })
        return res
