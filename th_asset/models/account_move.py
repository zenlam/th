# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    asset_transfer_id = fields.Many2one(
        'asset.account.transfer',
        string="Asset Transferred",
        readonly=True,
    )

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if res.stock_move_id.scrap_picking_id:
            res.ref = res.stock_move_id.scrap_picking_id.name
        return res
