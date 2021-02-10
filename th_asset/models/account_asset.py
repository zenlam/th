# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset.custom"

    account_analytic_id = fields.Many2one(required=True)
    capitalised_later = fields.Boolean('Capitalized Later?')
    asset_prepayment_account = fields.Many2one(
        'account.account', related='company_id.asset_prepayment_account')
    custom_source_department_id = fields.Many2one(
        'stock.location', string="Source Location"
    )
    asset_id_number = fields.Char(string="Identification Number")
    asset_desc = fields.Text(string="Description")
    depreciation_rate = fields.Float(string="Depreciation Rate", readonly=True)
    transfer_from_number = fields.Char(
        string="Transfer From", readonly=True
    )
    product_id = fields.Many2one('product.product', string='Product',
                                 readonly=True)
    transfer_posting_count = fields.Integer(compute='_transfer_posting_count',
                                            string='# Transfer Posting')
    origin_asset_id = fields.Integer(string="Origin Asset ID")
    quantity = fields.Integer(string="Quantity")
    purchase_date = fields.Date(string="Purchase Date")
    value_residual = fields.Float(store=True)

    depreciated_value = fields.Float(
        compute='_compute_depreciation_values',
        digits=dp.get_precision('Account'),
        string='Depreciated Value',
        store=True)
    depreciation_base = fields.Float(
        compute='_compute_depreciation_base',
        digits=dp.get_precision('Account'),
        string='Depreciation Base',
        store=True,
        help="This amount represent the depreciation base "
             "of the asset (Purchase Value - Salvage Value.")

    @api.depends('depreciation_line_ids.move_check',
                 'depreciation_line_ids.amount')
    @api.multi
    def _compute_depreciation_values(self):
        total_amount = 0.0
        for asset in self:
            for line in asset.depreciation_line_ids:
                if line.move_check:
                    total_amount += line.amount
            asset.depreciated_value = total_amount

    @api.depends('salvage_value')
    @api.multi
    def _compute_depreciation_base(self):
        for asset in self:
            # if asset.method in ['linear-limit', 'degr-limit']:
            #     asset.depreciation_base = asset.purchase_value
            # else:
            asset.depreciation_base = \
                asset.value - asset.salvage_value

    @api.multi
    def validate(self):
        """
        Called when confirm button is clicked in asset form.
        Create entry for capitalised_later asset.
        Close the asset if the residual value is 0.
        """
        res = super(AccountAssetAsset, self).validate()
        for asset in self:
            if asset.currency_id.is_zero(asset.value_residual):
                asset.state = 'close'
            if asset.method_number:
                if asset.method == 'linear':
                    asset.depreciation_rate = float(1 / asset.method_number)
                else:
                    asset.depreciation_rate = asset.method_progress_factor
            if asset.capitalised_later:
                debit_vals = {
                    'name': asset.name,
                    'debit': abs(asset.value),
                    'credit': 0.0,
                    'account_id': asset.category_id.account_asset_id.id,
                }
                credit_vals = {
                    'name': asset.name,
                    'debit': 0.0,
                    'credit': abs(asset.value),
                    'account_id': asset.asset_prepayment_account.id,
                }
                vals = {
                    'journal_id': asset.category_id.journal_id.id,
                    'date': asset.date,
                    'state': 'draft',
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = asset.env['account.move'].create(vals)
                move.post()
        return res

    @api.multi
    def update_capitalized_checkbox(self):
        """
        Open up a wizard to confirm de-selection of capitalised_later checkbox
        in asset form.
        """
        return {
            'name': _('Capitalized Asset Confirmation'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'asset.form.capitalised.wizard',
            'target': 'new',
            'context': self.env.context
        }

    def action_create_receiving_asset(self):
        for rec in self:
            new_depreciation_lines = []
            for line in rec.depreciation_line_ids:
                new_line = line.copy()
                new_depreciation_lines.append(new_line.id)
            vals = {
                'name': rec.name,
                'code': rec.invoice_id.number or False,
                'category_id': rec.category_id.id,
                'value': rec.value,
                'partner_id': rec.invoice_id.partner_id.id,
                'company_id': rec.invoice_id.company_id.id,
                'currency_id': rec.invoice_id.company_currency_id.id,
                'date': rec.invoice_id.date_invoice,
                'invoice_id': rec.invoice_id.id,
                'origin_asset_id': rec.id,
                'transfer_from_number': rec.custom_number,
                'depreciation_line_ids': [(6, 0, new_depreciation_lines)],
            }
            changed_vals = self.env[
                'account.asset.asset.custom'].onchange_category_id_values(
                vals['category_id'])
            vals.update(changed_vals['value'])
            if vals.get('invoice_id'):
                vals['account_analytic_id'] = \
                    rec.account_analytic_id.id or False
            asset = self.env['account.asset.asset.custom'].create(vals)
            if rec.category_id.open_asset:
                asset.validate()
        return True

    @api.multi
    def open_transfer_posting(self):
        move_ids = []
        asset_transfer = self.env['asset.accountability.transfer'].search([
            '|',
            ('transferred_asset_id', '=', self.id),
            ('transferred_asset_id', '=', self.origin_asset_id)
        ])
        for move_id in asset_transfer.move_ids:
            if move_id.id:
                move_ids.append(move_id.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }

    @api.multi
    def _transfer_posting_count(self):
        asset_transfer = self.env['asset.accountability.transfer'].search([
            '|',
            ('transferred_asset_id', '=', self.id),
            ('transferred_asset_id', '=', self.origin_asset_id)
        ])
        for asset in self:
            res = self.env['account.move'] \
                .search_count([('asset_transfer_id', '=', asset_transfer.id),
                               ('asset_transfer_id', '!=', False)])
            asset.transfer_posting_count = res or 0

    @api.multi
    def th_action_view_asset_traceability(self):
        self.ensure_one()
        stock_move_ids = self.env['stock.move'].search(
            [('product_id', '=', self.product_id)])
        domain = stock_move_ids
        action = self.env.ref(
            'stock.report_stock_inventory_print').read()[0]
        action['domain'] = [('product_id', 'in', domain)]
        return action


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category.custom'

    account_analytic_id = fields.Many2one(required=True)


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line.custom'

    account_analytic_id = fields.Many2one(required=True)
    move_status = fields.Selection(string='Move Status',
                                   readonly=True,
                                   related='move_id.state')
