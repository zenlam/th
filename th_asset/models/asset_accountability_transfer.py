# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssetAccountTransfer(models.Model):
    _inherit = "asset.accountability.transfer"

    source_department_id = fields.Many2one('stock.location')
    destination_department_id = fields.Many2one('stock.location')
    receiving_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Receiving Analytic Account",
        state={'done': [('readonly', True)]}
    )
    operation_type_id = fields.Many2one(
        'stock.picking.type',
        string="Operation Type",
        states={'draft': [('readonly', False)]}
    )
    move_ids = fields.One2many(
        'account.move',
        'asset_transfer_id',
        string='Transfer Reference',
        readonly=True)

    @api.onchange('destination_department_id')
    def onchange_receiving_analytic_id(self):
        for rec in self:
            rec.receiving_analytic_account_id = \
                rec.destination_department_id.account_analytic_id

    @api.onchange('source_department_id')
    def onchange_operation_type(self):
        res = {}
        src_location = self.source_department_id.id
        res['domain'] = {'operation_type_id': [
            ('default_location_src_id', '=', src_location),
            ('code', '=', 'internal')]}
        return res

    @api.onchange('transferred_asset_id')
    def onchange_transferred_asset_id(self):
        for rec in self:
            rec.source_partner_id = rec.transferred_asset_id\
                .custom_source_partner_id.id
            rec.source_department_id = rec.transferred_asset_id\
                .custom_source_department_id.id
            rec.analytic_account_id = rec.transferred_asset_id\
                .account_analytic_id.id

    @api.multi
    def act_approval(self):
        res = super(AssetAccountTransfer, self).act_approval()
        for rec in res:
            rec._generate_asset_transfer_picking()

    @api.multi
    def act_done(self):
        res = super(AssetAccountTransfer, self).act_done()
        for rec in self:
            if rec.operation_type_id.code == 'internal':
                depreciation_value = sum(
                    l.amount for l in rec.transferred_asset_id
                        .depreciation_line_ids if
                    l.move_check and not l.init_entry)

                acquisition_debit_vals = {
                    'name': rec.transferred_asset_id.name,
                    'partner_id': rec.destination_partner_id.id,
                    'debit': abs(rec.transferred_asset_id.value),
                    'credit': 0.0,
                    'analytic_account_id': rec.receiving_analytic_account_id.id,
                    'account_id':
                        rec.transfer_asset_category_id.account_asset_id.id,
                }
                acquisition_credit_vals = {
                    'name': rec.transferred_asset_id.name,
                    'partner_id': rec.source_partner_id.id,
                    'debit': 0.0,
                    'credit': abs(rec.transferred_asset_id.value),
                    'analytic_account_id': rec.analytic_account_id.id,
                    'account_id':
                        rec.transfer_asset_category_id.account_asset_id.id,
                }
                acquisition_vals = {
                    'journal_id': rec.transfer_asset_category_id.journal_id.id,
                    'date': fields.Date.today(),
                    'ref': rec.name,
                    'asset_transfer_id': rec.id,
                    'state': 'draft',
                    'line_ids': [(0, 0, acquisition_debit_vals),
                                 (0, 0, acquisition_credit_vals)]
                }
                acquisition_move = self.env['account.move'].create(
                    acquisition_vals)
                acquisition_move.post()

                if depreciation_value > 0:
                    depr_debit_vals = {
                        'name': rec.transferred_asset_id.name,
                        'partner_id': rec.destination_partner_id.id,
                        'debit': abs(depreciation_value),
                        'credit': 0.0,
                        'analytic_account_id': rec.receiving_analytic_account_id.id,
                        'account_id':
                            rec.transfer_asset_category_id.account_asset_id.id,
                    }
                    depr_credit_vals = {
                        'name': rec.transferred_asset_id.name,
                        'partner_id': rec.source_partner_id.id,
                        'debit': 0.0,
                        'credit': abs(depreciation_value),
                        'analytic_account_id': rec.analytic_account_id.id,
                        'account_id':
                            rec.transfer_asset_category_id.account_asset_id.id,
                    }
                    depr_vals = {
                        'journal_id': rec.transfer_asset_category_id.journal_id.id,
                        'date': fields.Date.today(),
                        'ref': rec.name,
                        'asset_transfer_id': rec.id,
                        'state': 'draft',
                        'line_ids': [(0, 0, depr_debit_vals),
                                     (0, 0, depr_credit_vals)]
                    }
                    acc_depr_debit_vals = {
                        'name': rec.transferred_asset_id.name,
                        'partner_id': rec.destination_partner_id.id,
                        'debit': abs(depreciation_value),
                        'credit': 0.0,
                        'analytic_account_id': rec.analytic_account_id.id,
                        'account_id':
                            rec.transfer_asset_category_id.account_asset_id.id,
                    }
                    acc_depr_credit_vals = {
                        'name': rec.transferred_asset_id.name,
                        'partner_id': rec.source_partner_id.id,
                        'debit': 0.0,
                        'credit': abs(depreciation_value),
                        'analytic_account_id': rec.receiving_analytic_account_id.id,
                        'account_id':
                            rec.transfer_asset_category_id.account_asset_id.id,
                    }
                    acc_depr_vals = {
                        'journal_id': rec.transfer_asset_category_id.journal_id.id,
                        'date': fields.Date.today(),
                        'ref': rec.name,
                        'asset_transfer_id': rec.id,
                        'state': 'draft',
                        'line_ids': [(0, 0, acc_depr_debit_vals),
                                     (0, 0, acc_depr_credit_vals)]
                    }
                    depr_move = self.env['account.move'].create(depr_vals)
                    acc_depr_move = self.env['account.move'].create(
                        acc_depr_vals)
                    depr_move.post()
                    acc_depr_move.post()
            rec.transferred_asset_id.state = 'close'
            rec.transferred_asset_id.action_create_receiving_asset()
        return res

    def _generate_asset_transfer_picking(self):
        picking_vals = self._prepare_picking_vals()
        picking = self.env['stock.picking'].create(picking_vals)
        move_vals = self._prepare_move_vals(picking)
        self.env['stock.move'].create(move_vals)

        return picking

    def _prepare_picking_vals(self):
        vals = {
            'location_id': self.source_department_id.id,
            'location_dest_id': self.destination_department_id.id,
            'picking_type_id': self.operation_type_id.id,
            'origin': self.name,
        }
        return vals

    def _prepare_move_vals(self, picking):
        vals = {
            'name': '/',
            'product_id': self.transferred_asset_id.product_id.id,
            'product_uom_qty': self.transferred_asset_id.quantity,
            'product_uom': self.transferred_asset_id.product_id.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'account_analytic_id': self.receiving_analytic_account_id.id,
        }
        return vals


class AssetTransferType(models.Model):
    _inherit = "asset.transfer.type"

    active = fields.Boolean(default=True)

    @api.constrains('code')
    def _check_duplicate_code(self):
        for type in self:
            transfer_type = self.search([
                ('code', '=', type.code),
                ('active', '=', type.active),
                ('id', '!=', type.id)])
            if type.active and type.code and transfer_type:
                raise ValidationError(_('This Asset Transfer Type already '
                                        'exists. \n'
                                        'Please change the code.'))

    @api.multi
    def toggle_active(self):
        res = super(AssetTransferType, self).toggle_active()
        for type in self:
            transfer_type = self.search([
                ('code', '=', type.code),
                ('active', '=', type.active),
                ('id', '!=', type.id)])
            if type.active and type.code and transfer_type:
                raise ValidationError(_('This Asset Transfer Type already '
                                        'exists. \n'
                                        'Please change the code.'))
        return res

    @api.multi
    def write(self, vals):
        res = super(AssetTransferType, self).write(vals)
        for type in self:
            if 'active' in vals:
                transfer_type = self.search([
                    ('code', '=', type.code),
                    ('active', '=', type.active),
                    ('id', '!=', type.id)])
                if type.active and type.code and transfer_type:
                    raise ValidationError(_('This Asset Transfer Type already '
                                            'exists. \n'
                                            'Please change the code.'))
        return res
