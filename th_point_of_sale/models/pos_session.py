# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round


class PosSession(models.Model):
    _inherit = 'pos.session'

    picking_id = fields.Many2one(comodel_name='stock.picking', string='Picking')
    refund_picking_id = fields.Many2one(comodel_name='stock.picking', string='Refund Picking')
    outlet_id = fields.Many2one('stock.warehouse', related='config_id.outlet_id', string='Outlet', store=True)

    @api.multi
    def action_pos_session_close(self):
        res = super(PosSession, self).action_pos_session_close()
        self.with_context(normal_picking=True, is_pos_picking=True, ignore_quant_reserve_validation=True).create_picking()
        self.with_context(refund_picking=True, is_pos_picking=True, ignore_quant_reserve_validation=True).create_picking()
        return res

    def _prepare_consolidated_orders(self):
        """

        :return: pos.order(...)
        """
        if self.env.context.get('normal_picking'):
            return self.order_ids.filtered(lambda x: not x.picking_id and not x.is_refund)
        elif self.env.context.get('refund_picking'):
            return self.order_ids.filtered(lambda x: not x.picking_id and x.is_refund)

    @api.multi
    def create_picking(self):
        """
        Consolidate all pickings from pos order then post them
        :return:
        """
        for session in self:
            move_qties = {}
            to_picking_orders = session._prepare_consolidated_orders()
            for order in to_picking_orders:
                for line in order.ingredient_lines:
                    if line.product_id and line.product_id.type not in ['product', 'consu']:
                        continue
                    # Consolidate all orderlines base on product and uom
                    key = (line.product_id.id, line.product_id.uom_id.id, line.standard_price)
                    # If stock ingredient qty is not 0 then only (eg optional product with NO sugar)
                    if line.inv_deduction_qty != 0:
                        if key not in move_qties:
                            move_qties[key] = line.inv_deduction_qty
                        else:
                            move_qties[key] += line.inv_deduction_qty

            if move_qties:
                picking_vals = session.prepare_picking_vals(move_qties)
                picking = self.env['stock.picking'].create(picking_vals)
                if picking:
                    to_picking_orders._force_picking_done(picking)
                    if self.env.context.get('normal_picking'):
                        session.write({'picking_id': picking.id})
                    elif self.env.context.get('refund_picking'):
                        session.write({'refund_picking_id': picking.id})


    def prepare_picking_vals(self, move_qties):
        """
        :param move_qties: qty of grouped moves
        :return:
        """
        moves = []
        config = self.config_id
        picking_type = config.picking_type_id
        return_pick_type = config.picking_type_id.return_picking_type_id or config.picking_type_id
        location = self.outlet_id.lot_stock_id
        outlet = self.outlet_id
        analytic_account_id = outlet and outlet.analytic_account_id and outlet.analytic_account_id.id or False
        if not analytic_account_id:
            raise ValidationError("Please configure analytic account for outlet %s "%(outlet.name))
        # Get destination location from outlet
        if (not picking_type) or (not picking_type.default_location_dest_id):
            customerloc, supplierloc = self.env['stock.warehouse']._get_partner_locations()
            destination_id = customerloc.id
        else:
            destination_id = picking_type.default_location_dest_id.id
        for key in move_qties:
            moves.append(
                (0, 0, {
                    'name': self.name,
                    'product_uom': key[1],
                    'order_todo_uom': key[1],
                    'order_todo_qty': abs(move_qties[key]),
                    'delivered_received_uom': key[1],
                    'price_unit': key[2], # just keep here price_unit in case of same session hase different price [importnant to keep here to split same product the moves]
                    'while_consolidate_outlet_price_unit': key[2], # just keep here price_unit in case of same session hase different price [importnant to keep here to split same product the moves]
                    'picking_type_id': picking_type.id if move_qties[key] >= 0 else return_pick_type.id,
                    'product_id': key[0],
                    'product_uom_qty': abs(move_qties[key]),
                    'state': 'draft',
                    'location_id': location.id if move_qties[key] >= 0 else destination_id,
                    'location_dest_id':  destination_id if move_qties[key] >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location.id,
                    'date_expected': self.start_at,
                    'account_analytic_id': analytic_account_id
                })
            )

        picking_vals = {
            'analytic_account_id': analytic_account_id,
            'move_lines': moves,
            'origin': self.name,
            'date_done': self.start_at,
            'min_date': self.start_at,
            'picking_type_id': picking_type.id,
            'company_id': config.company_id.id,
            'move_type': 'direct',
            'location_id': location.id,
            'location_dest_id': destination_id,
        }
        if self.env.context.get('refund_picking'):
            picking_vals.update({
                'location_id': destination_id,
                'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location.id,
                'picking_type_id': return_pick_type.id
            })
        return picking_vals





    # @api.multi
    # def action_pos_session_close(self):
    #     """ This function will be triggered when closing a pos session.
    #     Note: Need to override this function in order to pass analytic account in the context
    #     """
    #     # Close CashBox
    #     for session in self:
    #         company_id = session.config_id.company_id.id
    #         analytic_account_id = session.config_id.outlet_id.analytic_account_id.id
    #         ctx = dict(self.env.context, force_company=company_id, company_id=company_id,
    #                    analytic_account_id=analytic_account_id)
    #         ctx_notrack = dict(ctx, mail_notrack=True)
    #         for st in session.statement_ids:
    #             if abs(st.difference) > st.journal_id.amount_authorized_diff:
    #                 # The pos manager can close statements with maximums.
    #                 if not self.user_has_groups("point_of_sale.group_pos_manager"):
    #                     raise UserError(_(
    #                         "Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (
    #                                         st.difference, st.journal_id.amount_authorized_diff))
    #             if (st.journal_id.type not in ['bank', 'cash']):
    #                 raise UserError(_("The journal type for your payment method should be bank or cash."))
    #             st.with_context(ctx_notrack).sudo().button_confirm_bank()
    #     self.with_context(ctx)._confirm_orders()
    #     self.write({'state': 'closed'})
    #     return {
    #         'type': 'ir.actions.client',
    #         'name': 'Point of Sale Menu',
    #         'tag': 'reload',
    #         'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
    #     }