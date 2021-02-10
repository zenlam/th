# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID


class Company(models.Model):
    _inherit = 'res.company'

    @api.model
    def create(self, vals):
        """
        Create analytic account upon the company creation
        """
        # get the analytic account vals
        analytic_account_vals = self.prepare_analytic_account_vals(vals)
        analytic_account_id = \
            self.env['account.analytic.account'].create(analytic_account_vals)
        self = self.with_context(create_from_company=True,
                                 analytic_account=analytic_account_id.id)
        company = super(Company, self).create(vals)
        # need to write the company id to the analytic account
        analytic_account_id.write({
            'company_id': company.id,
        })
        return company

    def prepare_analytic_account_vals(self, vals):
        """
        Prepare analytic account creation dictionary
        """
        return {
            'name': vals.get('name'),
            'currency_id': vals.get('currency_id'),
        }


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def _get_picking_type_create_values(self, max_sequence):
        data, next_sequence = super(StockWarehouse, self)._get_picking_type_create_values(max_sequence)
        for key in data:
            if 'use_existing_lots' in data[key]:
                data[key]['use_existing_lots'] = True
            if 'use_create_lots' in data[key]:
                data[key]['use_create_lots'] = True

        return data, max_sequence

    @api.model
    def create(self, vals):
        """
        If the stock warehouse is created from company creation, then use the
        analytic account from context.
        """
        context = self.env.context
        if context.get('create_from_company') and \
                context.get('analytic_account'):
            vals.update({
                'analytic_account_id': context.get('analytic_account'),
            })
        return super(StockWarehouse, self).create(vals)