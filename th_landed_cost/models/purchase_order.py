# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_caln_factor = fields.Boolean(string="Caln Factor Applied",
                                    default=False)
    caln_factor = fields.Float(string="Caln Factor(%)")
    landed_cost_count = fields.Integer(string="Landed Cost Count",
                                       compute='_compute_lcost_count')
    landed_cost_type = fields.Selection([('percentage', 'Percentage'),
                                         ('amount', 'Amount')],
                                        string='Landed Cost Type')
    lc_amount_apply = fields.Float(string='Final Landed Cost Amount',
                                   readonly=True, store=True,
                                   compute='compute_lc_amount_apply')

    @api.multi
    def write(self, vals):
        """
        Update the landed cost settings in Picking if these
        settings change in PO (only incoming picking and picking not in done
        state will be updated)

        Validation of caln factor, cannot be negative
        """
        if ('is_caln_factor' in vals) or ('caln_factor' in vals) or (
                'landed_cost_type' in vals):
            for record in self:
                if vals.get('is_caln_factor',
                            record.is_caln_factor) and vals.get('caln_factor',
                                                                False) < 0:
                    raise UserError(_("Caln Factor can't be Negative!"))
                for picking in record.picking_ids:
                    if picking.state == 'done':
                        continue
                    if picking.picking_type_code == 'incoming':
                        picking.is_caln_factor = vals.get(
                            'is_caln_factor', record.is_caln_factor)
                        picking.caln_factor = vals.get(
                            'caln_factor', record.caln_factor)
                        picking.landed_cost_type = \
                            vals.get('landed_cost_type'
                                     , record.landed_cost_type)
        res = super(PurchaseOrder, self).write(vals)
        return res

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        super(PurchaseOrder, self).onchange_partner_id()
        if self.partner_id:
            self.is_caln_factor = self.caln_factor \
                = self.partner_id.landed_cost_factor
            self.landed_cost_type = self.partner_id.landed_cost_type

    @api.multi
    def _compute_lcost_count(self):
        for record in self:
            record.landed_cost_count = self.env[
                'stock.landed.cost'].search_count(
                [('purchase_order_id', '=', record.id)])

    @api.multi
    def action_view_landed_cost(self):
        self.ensure_one()
        landed_cost_ids = self.env[
            'stock.landed.cost'].search(
            [('purchase_order_id', '=', self.id)])
        action = self.env.ref(
            'stock_landed_costs.action_stock_landed_cost').read()[0]
        action['domain'] = [('id', 'in', landed_cost_ids.ids)]
        return action

    @api.model
    def _prepare_picking(self):
        """
        Inherit this function to pass landed cost fields to Picking when we
        create Picking from PO, based on landed cost settings in PO
        """
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({'is_caln_factor': self.is_caln_factor,
                    'caln_factor': self.caln_factor,
                    'landed_cost_type': self.landed_cost_type})
        return res

    @api.multi
    def button_confirm(self):
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

        return super(PurchaseOrder, self).button_confirm()

    @api.multi
    @api.depends('caln_factor', 'amount_untaxed', 'landed_cost_type')
    def compute_lc_amount_apply(self):
        for record in self:
            if record.landed_cost_type == 'percentage':
                record.lc_amount_apply = record.amount_untaxed * \
                                         record.caln_factor / 100
            else:
                record.lc_amount_apply = record.caln_factor
