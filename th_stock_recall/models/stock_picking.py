# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    recall_id = fields.Many2one(comodel_name='stock.recall', string=_('Recall'))

    @api.multi
    def action_cancel(self):
        """
        Cancel Recall if all of pickings is cancelled
        :return:
        """
        res = super(StockPicking, self).action_cancel()
        for r in self:
            if r.recall_id.id and r.recall_id.state != 'cancelled' and all(r.recall_id.picking_ids.mapped(lambda p: p.state == 'cancel')):
                r.recall_id.button_cancel()
        return res

    @api.multi
    def button_validate(self):
        """
        Push recall to done if all of pickings is done
        :return:
        """
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.recall_id.id and picking.recall_id.state == 'pending' and all(picking.recall_id.picking_ids.mapped(lambda p: p.state == 'done')):
                picking.recall_id.action_done()
        return res
