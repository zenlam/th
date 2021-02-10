# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self.with_context({'product_tmpl_id':self.product_id.product_tmpl_id.id}))._prepare_stock_moves(picking)
        for re in res:
            if 'order_todo_qty' not in re.keys():
                re['order_todo_qty'] = self.product_qty
            if 'order_todo_uom' not in re.keys():
                re['order_todo_uom'] = self.product_uom.id
            if 'delivered_received_uom' not in re.keys():
                re['delivered_received_uom'] = self.product_uom.id
            if 'delivered_received_uom_initial' not in re.keys():
                re['delivered_received_uom_initial'] = self.product_uom.id
        return res
