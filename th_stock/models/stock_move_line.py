# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=1)
    stock_request_lot_id = fields.Many2one('stock.production.lot',
                                           string="Lot/Serial Number")
    stock_request_removal_date = fields.Date(
        related='stock_request_lot_id.removal_date',
        string='Expiry Date'
    )
    scrap_picking_id = fields.Many2one('scrap.picking')

    # @api.onchange('stock_request_lot_id')
    # def onchange_sr_lot_id(self):
    #     if self.picking_id.is_stock_transfer and self.stock_request_lot_id:
    #         self.lot_id = self.stock_request_lot_id
    #         # check availability once again with new lot id
    #         self.picking_id.action_assign()

    def prepare_stock_moves_vals(self, vals):
        """ This will return the stock move values dictionary to function create
        """
        picking = self.env['stock.picking'].browse(vals['picking_id'])
        product = self.env['product.product'].browse(vals['product_id'])
        return {
            'name': _('New Move:') + product.display_name,
            'product_id': product.id,
            'product_uom_qty': 'qty_done' in vals and vals['qty_done'] or 0,
            'product_uom': vals['product_uom_id'],
            'location_id': 'location_id' in vals and vals['location_id'] or picking.location_id.id,
            'location_dest_id': 'location_dest_id' in vals and vals[
                'location_dest_id'] or picking.location_dest_id.id,
            'state': 'done',
            'additional': True,
            'picking_id': picking.id,
            # Need to pass account_analytic_id to create stock move
            'account_analytic_id': vals['account_analytic_id']
        }

    @api.model_create_multi
    def create(self, vals_list):
        """ This function will create stock move line.
        Note: Will not override the whole function due to this create function is inherited in stock_account. Will
        inherit this create function so it will not break the create function from stock_account.
        """
        for vals in vals_list:

            # If the move line is directly create on the picking view.
            # If this picking is already done we should generate an
            # associated done move.
            if 'picking_id' in vals and not vals.get('move_id'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.state == 'done':
                    new_move_vals = self.prepare_stock_moves_vals(vals)
                    new_move = self.env['stock.move'].create(new_move_vals)
                    vals['move_id'] = new_move.id
        return super(StockMoveLine, self).create(vals_list)
