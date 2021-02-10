# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request")

    @api.multi
    def update_deliver_qty_on_purchase_request(self):
        picking_order_lines = {}
        for line in self.move_lines:
            if line.product_id.id not in picking_order_lines.keys():
                picking_order_lines[line.product_id.id] = line.delivered_received_qty
            else:
                picking_order_lines[line.product_id.id] += line.delivered_received_qty

        for pr_line in self.purchase_request_id.purchase_request_line_ids:
            if pr_line.product_id.id in picking_order_lines.keys():
                pr_line.delivered_qty = picking_order_lines[pr_line.product_id.id]


    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for pick in self:
            if pick.purchase_request_id:
                pick.purchase_request_id.state = 'done'
                pick.update_deliver_qty_on_purchase_request()
        return res
