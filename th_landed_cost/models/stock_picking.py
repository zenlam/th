# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_caln_factor = fields.Boolean(string="Caln Factor Applied",
                                    default=False, readonly=True)
    caln_factor = fields.Float(string="Caln Factor(%)", readonly=True)
    landed_cost_count = fields.Integer(string="Landed Cost Count",
                                       compute='_compute_lcost_count')
    landed_cost_type = fields.Selection([('percentage', 'Percentage'),
                                         ('amount', 'Amount')],
                                        string='Landed Cost Type',
                                        default='percentage',
                                        readonly=True)
    lc_amount_apply = fields.Float(string='Final Landed Cost Amount',
                                   readonly=True, store=True,
                                   compute='compute_lc_amount_apply')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    @api.multi
    @api.depends('caln_factor', 'move_ids_without_package.quantity_done',
                 'move_ids_without_package.product_qty', 'landed_cost_type')
    def compute_lc_amount_apply(self):
        for record in self:
            moves = record.move_ids_without_package
            total_price = 0
            total_qty = 0
            total_qty_done = 0
            for move in moves:
                # get order qty
                total_qty += move.purchase_line_id.product_uom_qty
                if move.quantity_done > 0:
                    # get total price for percentage, total qty_done for amount
                    total_price += move.quantity_done * move.price_unit
                    total_qty_done += move.quantity_done
                else:
                    total_price += move.product_qty * move.price_unit
                    total_qty_done += move.product_qty
            # skip picking that has no purchase_line_id
            if total_qty == 0:
                continue
            if record.landed_cost_type == 'percentage':
                record.lc_amount_apply = total_price * \
                                         record.caln_factor / 100
            else:
                record.lc_amount_apply = \
                    record.caln_factor / total_qty * total_qty_done

    @api.multi
    def _compute_lcost_count(self):
        for record in self:
            self.landed_cost_count = self.env[
                'stock.landed.cost'].search_count(
                [('picking_ids', '=', record.id)])

    @api.multi
    def action_view_landed_cost(self):
        self.ensure_one()
        landed_cost_ids = self.env[
            'stock.landed.cost'].search(
            [('picking_ids', '=', self.id)])
        action = self.env.ref(
            'stock_landed_costs.action_stock_landed_cost').read()[0]
        action['domain'] = [('id', 'in', landed_cost_ids.ids)]
        return action

    @api.multi
    def action_view_journal_item(self):
        self.ensure_one()
        landed_cost_ids = self.env[
            'stock.landed.cost'].search(
            [('picking_ids', '=', self.id)])
        action = self.env.ref(
            'account.action_account_moves_all_a').read()[0]
        action['domain'] = ['|', ('ref', '=', self.name),
                            ('ref', 'in', [x.name for x in landed_cost_ids])]
        return action

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for record in self:
            if record.is_caln_factor:
                record._apply_landed_cost()
        return True

    @api.multi
    def _apply_landed_cost(self):
        vals = self._prepare_landed_cost_vals()
        landed_cost = self.env['stock.landed.cost'].create(vals)
        landed_cost.compute_landed_cost()
        landed_cost.button_validate()
        return

    @api.multi
    def _prepare_landed_cost_vals(self):
        acc_journal_id = self.company_id.default_lcost_journal
        cost_line_vals = self._prepare_cost_line_vals()
        return {
            'date': datetime.now(),
            'picking_ids': [(4, self.id)],
            'account_journal_id': acc_journal_id.id,
            'purchase_order_id': self.purchase_id.id,
            'cost_lines': [(0, 0, cost_line_vals)]
        }

    @api.multi
    def _prepare_cost_line_vals(self):
        product_id = self.company_id.default_caln_factor_product
        return {
            'product_id': product_id.id,
            'name': product_id.name or '',
            'split_method': product_id.split_method or 'equal',
            'account_id': product_id.property_account_expense_id.id or
                          product_id.categ_id.property_account_expense_categ_id.id,
            'price_unit': self.lc_amount_apply
        }

    @api.multi
    def button_validate(self):
        """
        Inherit this function to validate the following fields is configured:
        1) Default Landed Cost Product
        2) Default Landed Cost Journal
        3) Expense Account of the Default Landed Cost Product
        """
        if self.is_caln_factor:
            for record in self:
                if not record.company_id.default_caln_factor_product:
                    raise UserError(_(
                        'You have to configure a default Landed'
                        ' Cost Product in settings.'))
                if not record.company_id.default_lcost_journal:
                    raise UserError(_(
                        'You have to configure a '
                        'default Account Journal for landed cost in settings.'))
                if not record.company_id.default_caln_factor_product. \
                        property_account_expense_id:
                    raise UserError(_(
                        'You have to configure a '
                        'expense account for the default landed cost product, %s.')
                                    % record.company_id.
                                    default_caln_factor_product.name)

        return super(StockPicking, self).button_validate()
