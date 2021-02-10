# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockOverProcessedTransfer(models.TransientModel):
    _inherit = 'stock.overprocessed.transfer'

    overprocessed_product_name = fields.Text(compute='_compute_overprocessed_product_name',
                                             readonly=True)

    @api.multi
    def _compute_overprocessed_product_name(self):
        for wizard in self:
            moves = wizard.picking_id._get_overprocessed_stock_moves()
            string = ""
            for move in moves:
                string += move.product_id.display_name + ' - ' + str(move.quantity_done - move.product_uom_qty) + ' ' + move.product_uom.name + '\n'

            wizard.overprocessed_product_name = string


    # def _get_overprocessed_stock_moves(self):
    #     self.ensure_one()
    #     return self.move_lines.filtered(
    #         lambda move: move.product_uom_qty != 0 and float_compare(move.quantity_done, move.product_uom_qty,
    #                                                                  precision_rounding=move.product_uom.rounding) == 1
    #     )
