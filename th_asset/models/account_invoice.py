# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import Warning

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_prepayment_account = fields.Many2one(
        'account.account', related='company_id.asset_prepayment_account')
    capitalised_later = fields.Boolean('Capitalized Later?')

    @api.onchange('capitalised_later')
    def set_invoice_line_account(self):
        """
        Change the account to prepayment account when the capitalised_later
        checkbox is selected. Change back to product account when
        capitalised_later checkbox deselected.
        """
        if self.capitalised_later:
            self.account_id = self.asset_prepayment_account
        else:
            account = self.get_invoice_line_account(
                self.invoice_id.type, self.product_id,
                self.invoice_id.fiscal_position_id, self.invoice_id.company_id)
            if account:
                self.account_id = account.id

    @api.one
    def asset_create(self):
        """
        Overwrite the function and pass the capitalised_later and product_id
        over to asset when validating vendor bill.
        """
        if self.asset_category_id:
            vals = {
                'name': self.name,
                'code': self.invoice_id.number or False,
                'category_id': self.asset_category_id.id,
                'value': self.price_subtotal_signed,
                'partner_id': self.invoice_id.partner_id.id,
                'company_id': self.invoice_id.company_id.id,
                'currency_id': self.invoice_id.company_currency_id.id,
                'date': self.invoice_id.date_invoice,
                'invoice_id': self.invoice_id.id,
                'capitalised_later': self.capitalised_later,
                'product_id': self.product_id.id,
                'quantity': self.quantity,
                'depreciation_base': self.price_subtotal_signed,
            }
            changed_vals = self.env[
                'account.asset.asset.custom'].onchange_category_id_values(
                vals['category_id'])
            vals.update(changed_vals['value'])
            if vals.get('invoice_id'):
                vals[
                    'account_analytic_id'] = self.account_analytic_id.id or False
            asset = self.env['account.asset.asset.custom'].create(vals)
            if self.asset_category_id.open_asset:
                asset.validate()

            if asset:
                self.env['asset.accountability.transfer'].create({
                    'transferred_asset_id':asset.id,
                    'asset_transfer_type_id': self.env.ref('account_asset_extend_onnet.asset_transfer_to_stock_type').id,
                    'source_department_id': self.env.ref('account_asset_extend_onnet.hr_department_vendor').id,
                    'destination_department_id': self.env.ref('account_asset_extend_onnet.hr_department_stock').id,
                    'source_partner_id': asset.partner_id and asset.partner_id.id or False,
                    'destination_partner_id': self.env.ref('base.partner_admin').id
                    })
        return True

    @api.onchange('product_id')
    def set_product_asset_category(self):
        if self.product_id.is_asset:
            self.asset_category_id = self.product_id.asset_category_id


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    asset_count = fields.Integer(compute='_asset_count',
                                 string='# Asset')

    @api.multi
    def action_move_create(self):
        """
        Moved over from odoo_account_asset ( community module ) because the
        function action_move_create is overwrote in th_account module.
        """
        result = super(AccountInvoice, self).action_move_create()
        for inv in self:
            context = dict(self.env.context)
            # Within the context of an invoice,
            # this default value is for the type of the invoice, not the type of the asset.
            # This has to be cleaned from the context before creating the asset,
            # otherwise it tries to create the asset with the type of the invoice.
            context.pop('default_type', None)
            inv.invoice_line_ids.with_context(context).asset_create()
        return result

    @api.multi
    def open_asset_product(self):
        asset = self.env['account.asset.asset.custom'].search([
            ('invoice_id', '=', self.id)
        ])
        return {
            'name': _('Asset'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.asset.custom',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', asset.ids)],
        }

    @api.multi
    def _asset_count(self):
        for asset in self:
            res = self.env['account.asset.asset.custom'] \
                .search_count([('invoice_id', '=', self.id)])
            asset.asset_count = res or 0

    @api.multi
    def action_cancel(self):
        confirmed_assets = []
        assets = self.env['account.asset.asset.custom']\
            .search([('invoice_id', 'in', self.ids)])
        for asset in assets:
            if asset.state != 'draft':
                confirmed_assets.append(asset.id)
            else:
                asset.unlink()
        if confirmed_assets:
            return {
                'name': _('Vendor Bill Cancellation Validation for Asset'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'bill.asset.cancellation.wizard',
                'target': 'new',
                'context': self.env.context
            }
        return super(AccountInvoice, self).action_cancel()
