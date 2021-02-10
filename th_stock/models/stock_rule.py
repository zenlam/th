# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        """ Returns a dictionary of values that will be used to create a stock move from a procurement.
        Note: If the procurement source is sale order line, then pass the analytic account in the sale order to the
        stock move. This function will create stock move when the user confirms sale order.
        """
        res = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name,
                                                            origin, values, group_id)
        if values.get('sale_line_id'):
            sale_order_id = self.env['sale.order.line'].browse(values['sale_line_id']).order_id
            res.update({
                'account_analytic_id': sale_order_id.analytic_account_id.id,
            })
        return res