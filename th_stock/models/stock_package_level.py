# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockPackageLevel(models.Model):
    _inherit = "stock.package_level"

    def prepare_stock_move_line_vals(self, package_level, quant, corresponding_move):
        """ This will return the stock move line values dictionary to function _set_is_done
        """
        return {
            'location_id': package_level.location_id.id,
            'location_dest_id': package_level.location_dest_id.id,
            'picking_id': package_level.picking_id.id,
            'product_id': quant.product_id.id,
            'qty_done': quant.quantity,
            'product_uom_id': quant.product_id.uom_id.id,
            'lot_id': quant.lot_id.id,
            'package_id': package_level.package_id.id,
            'result_package_id': package_level.package_id.id,
            'package_level_id': package_level.id,
            'move_id': corresponding_move.id,
            # need to pass account_analytic_id to create stock move line
            'account_analytic_id': corresponding_move.account_analytic_id.id,
        }

    def _set_is_done(self):
        """ This function is to inverse the is_done field
        Note: Need to pass account_analytic_id to create stock move line
        """
        for package_level in self:
            if package_level.is_done:
                if not package_level.is_fresh_package:
                    for quant in package_level.package_id.quant_ids:
                        corresponding_ml = package_level.move_line_ids.filtered(lambda ml: ml.product_id == quant.product_id and ml.lot_id == quant.lot_id)
                        if corresponding_ml:
                            corresponding_ml[0].qty_done = corresponding_ml[0].qty_done + quant.quantity
                        else:
                            corresponding_move = package_level.move_ids.filtered(lambda m: m.product_id == quant.product_id)[:1]
                            new_move_line_vals = self.prepare_stock_move_line_vals(package_level, quant, corresponding_move)
                            self.env['stock.move.line'].create(new_move_line_vals)
            else:
                package_level.move_line_ids.filtered(lambda ml: ml.product_qty == 0).unlink()
                package_level.move_line_ids.filtered(lambda ml: ml.product_qty != 0).write({'qty_done': 0})