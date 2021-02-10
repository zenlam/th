# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID

class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def _compute_is_from_po(self):
        for picking in self:
            if picking.move_ids_without_package:
                if picking.move_ids_without_package[0].purchase_line_id.order_id:
                    picking.is_from_po = True

    havi_origin = fields.Char('HAVI Source Document', copy=False)
    havi_delivery_file = fields.Binary("Delivery Note Csv file",
                                help="This File is set by the Havi Logistic via EDI.")
    is_from_po = fields.Boolean(string='Is From PO',
                                compute='_compute_is_from_po')

    # NOTE : Need to overwite this function from base because inheritance is not feasible for new logic.
    def action_generate_backorder_wizard(self):
        no_backorder_picking = [p for p in self.filtered(lambda x : x.picking_type_id and x.picking_type_id.no_backorder)]
        view = self.env.ref('stock.view_backorder_confirmation')
        wiz = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, p.id) for p in self]})

        # if all of the picking is no backorder then we create back order and cancel it immediately same as odoo base else open no backorder wizard.
        if len(no_backorder_picking) == len(self):
            return wiz._process(cancel_backorder=True)
        else:
            return {
                'name': _('Create Backorder?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.backorder.confirmation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

    def prepare_stock_move_vals(self, ops, pick):
        """ This will return the stock move values dictionary to function action_done
        """
        return {
            'name': _('New Move:') + ops.product_id.display_name,
            'product_id': ops.product_id.id,
            'product_uom_qty': ops.qty_done,
            'product_uom': ops.product_uom_id.id,
            'location_id': pick.location_id.id,
            'location_dest_id': pick.location_dest_id.id,
            'picking_id': pick.id,
            'picking_type_id': pick.picking_type_id.id,
            # need to pass account_analytic_id to create stock move
            'account_analytic_id': ops.account_analytic_id.id,
        }

    @api.multi
    def action_done(self):
        """Changes picking state to done by processing the Stock Moves of the Picking
        Normally that happens when the button "Done" is pressed on a Picking view.
        Note: Will not override the whole function due to this create function is inherited in other modules.
        """
        # Check if there are ops not linked to moves yet
        for pick in self:
            # # Link existing moves or add moves when no one is related
            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
                # Search move with this product
                moves = pick.move_lines.filtered(lambda x: x.product_id == ops.product_id)
                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
                if moves:
                    ops.move_id = moves[0].id
                else:
                    new_move_val = self.prepare_stock_move_vals(ops, pick)
                    new_move = self.env['stock.move'].create(new_move_val)
                    ops.move_id = new_move.id
                    new_move._action_confirm()
        return super(Picking, self).action_done()


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    no_backorder = fields.Boolean('No Backorder', default=False, help='Do not allowed to create back order for this picking type.')
