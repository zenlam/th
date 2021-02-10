# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Inventory(models.Model):
    _inherit = "stock.inventory"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=1)

    def _get_inventory_lines_values(self):
        """ Create inventory lines based on the inventory adjustment configuration
        Note: This function will populate the inventory lines when the user starts the inventory
        """
        res = super(Inventory, self)._get_inventory_lines_values()
        for line in res:
            line.update({
                'account_analytic_id': self.account_analytic_id.id,
            })
        return res


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=1)

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        """ Create stock move based on the inventory lines
        Note: This function will create the stock moves when the user confirms the inventory
        """
        res = super(InventoryLine, self)._get_move_values(qty, location_id, location_dest_id, out)
        res.update({
            'account_analytic_id': self.account_analytic_id.id,
        })
        return res
