# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True,
                                          states={'done': [('readonly', True)]})
    menu_id = fields.Many2one('product.product', string='Menu')
    product_desc = fields.Char(related='product_id.name', string="Description")
    scrap_picking_id = fields.Many2one('scrap.picking')

    @api.multi
    def name_get(self):
        res = []
        for scrap in self:
            res.append((scrap.id, scrap.scrap_picking_id.name))
        return res

    def _prepare_move_values(self):
        """ This function will return dictionary of stock move values to do_scrap function.
        Note: Need to add analytic account in the dictionary
        """
        res = super(StockScrap, self)._prepare_move_values()
        res.update({
            'account_analytic_id': self.account_analytic_id.id,
            'name': self.origin,
            'scrap_picking_id': self.scrap_picking_id.id
        })
        if res.get('move_line_ids'):
            for move_line in res.get('move_line_ids'):
                move_line[2].update({
                    'account_analytic_id': self.account_analytic_id.id,
                    'scrap_picking_id': self.scrap_picking_id.id
                })
        return res
