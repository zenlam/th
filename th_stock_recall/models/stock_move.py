# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    recall_line_id = fields.Many2one(comodel_name='stock.recall.product', string='Recall Line')

    def _action_done(self):
        """
        To update qty_received_recall for recall line once picking done
        :return:
        """
        res = super(StockMove, self)._action_done()
        for r in self:
            if r.recall_line_id.id:
                r.recall_line_id.qty_received_recall += r.product_uom_qty
        return res
