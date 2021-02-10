# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import tempfile
import csv
import base64
import os


class OutletOrderingProductDeby(models.Model):
    _name = 'outlet.ordering.product.deny'

    @api.multi
    @api.depends('product_id', 'outlet_id')
    def _compute_name(self):
        for r in self:
            r.name = 'Restrict product {product} on outlet {outlet}'.format(
                product=r.product_id.name, outlet=r.outlet_id.name)

    @api.multi
    @api.depends('product_id.multi_uom_ids.barcode', 'product_id.multi_uom_ids.outlet_ordering')
    def _compute_havi_code(self):
        for r in self:
            r.havi_code = r.product_id.multi_uom_ids.filtered(lambda x: x.outlet_ordering)[0].barcode

    @api.multi
    @api.depends('product_id.multi_uom_ids.outlet_ordering')
    def _compute_ordering_uoms(self):
        for r in self:
            r.ordering_uom_ids = [(6, 0, r.product_id.multi_uom_ids.filtered(lambda x: x.outlet_ordering).ids)]

    name = fields.Char(string=_('Name'))
    type = fields.Selection(selection=[('allow', _("Allow")),
                                       ('deny', _('Deny'))], string=_('Type'), required=True)
    applied = fields.Selection(selection=[('outlet', _('Outlet')),
                                          ('area', _('Area'))], string='Applied for', required=True)
    outlet_ids = fields.Many2many(comodel_name='stock.warehouse', relation='product_outlet_restricted_rel',
                                  column1='deny_id', column2='outlet_id', string=_('Outlets'),
                                  domain=[('create_from', '=', 'outlet')])
    area_ids = fields.Many2many(comodel_name='res.country.area', relation='product_area_restricted_rel',
                                column1='deny_id', column2='area_id', string=_('Areas'))
    product_ids = fields.Many2many(comodel_name='product.product', relation='outlet_product_deny_rel',
                                   column1='deny_id', column2='product_id', string=_('Products'), required=True)
    product_category_ids = fields.Many2many(comodel_name='product.category', relation='outlet_product_categ_deny_rel',
                                            column1='deny_id', column2='category_id', string=_('Product Categories'), required=True)

    product_id = fields.Many2one(comodel_name='product.product', string=_('Product'), required=False)
    outlet_id = fields.Many2one(comodel_name='stock.warehouse', domain=[('create_from', '=', 'outlet')],
                                string=_('Outlet'), required=False)
    product_name = fields.Char(string=_('Product Name'), related='product_id.name')
    product_code = fields.Char(string=_('Product Code'), related='product_id.default_code')
    outlet_name = fields.Char(string=_('Outlet Name'), related='outlet_id.name')
    outlet_code = fields.Char(string=_('Outlet Code'), related='outlet_id.code')
    date_start = fields.Date(string=_('Start Date'))
    date_end = fields.Date(string=_('End Date'))
    th_code = fields.Char(string=_('TH Code'), related='product_id.barcode', readonly=True)
    ordering_uom_ids = fields.Many2many(comodel_name='product.multi.uom', compute='_compute_ordering_uoms',
                                        store=True, relation='product_deny_havi_code_rel',
                                        column1='deny_product_config_id',
                                        column2='multi_uom_id')
    havi_code = fields.Char(string=_('HAVI Code'), compute='_compute_havi_code', readonly=True)
    csv_data = fields.Binary(string=_('CSV Data'))
    csv_filename = fields.Char(string=_('CSV File'))

    _sql_constraints = [
        ('date_range_check', 'check (date_start <= date_end)',
         _('End date cannot earlier than start date')),
    ]

    def _get_config_products(self):
        """

        :return:
        """
        all_categ = self.env['product.category'].search([('parent_id', 'child_of', self.product_category_ids.ids)])
        all_products = self.env['product.product'].search([('categ_id', 'in', all_categ.ids)]) | self.product_ids
        if self.type == 'allow':
            return all_products
        else:
            return self.env['product.product'].search([('id', 'not in', all_products.ids)])

    def _get_config_outlets(self):
        """

        :return:
        """
        if self.applied == 'outlet':
            return self.outlet_ids
        else:
            return self.env['stock.warehouse'].search([('area_id', 'in', self.area_ids.ids),
                                                       ('create_from', '=', 'outlet')])

    @api.multi
    def generate_restricted_data(self):
        self.ensure_one()
        products = self._get_config_products()
        outlets = self._get_config_outlets()
        data = [['OUTLET CODE', 'OUTLET NAME', 'PRODUCT CODE', 'PRODUCT NAME',
                 'START DATE', 'END DATE', 'TH CODE', 'HAVI CODE']]
        for outlet in outlets:
            for product in products:
                ordering_uom = product.multi_uom_ids.filtered(lambda x: x.outlet_ordering)
                if ordering_uom:
                    ordering_uom = ordering_uom[0]
                row = [outlet.code or '', outlet.name or '', product.default_code or '', product.name or '',
                       self.date_start or '', self.date_end or '', product.barcode or '', ordering_uom.barcode or '']
                data.append(row)

        tmp_path = tempfile.mktemp(prefix='th.restrict.', suffix='.csv')
        with open(tmp_path, 'w') as f:
            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
            for row in data:
                wr.writerow(row)

        self.write({'csv_data': base64.b64encode(open(tmp_path, 'rb').read()),
                    'csv_filename': '{name}.csv'.format(name=self.name)})
        os.remove(tmp_path)
        return True

    # def _check_date_range(self):
    #     """
    #
    #     :return:
    #     """
    #     where_clause = ''
    #     conditions = []
    #     conditions.append('id != %s' % self.id)
    #     conditions.append("outlet_id = '%s'" % self.outlet_id.id)
    #     conditions.append("product_id = '%s'" % self.product_id.id)
    #     date_condition = []
    #     if self.date_start:
    #         date_condition.append("(date_end IS NOT NULL AND date_end < '%s'::date)" % self.date_start)
    #     if self.date_end:
    #         date_condition.append("(date_start IS NOT NULL AND date_start > '%s'::date)" % self.date_end)
    #     if date_condition:
    #         conditions.append('NOT (%s)' % ' OR '.join(date_condition))
    #
    #     where_clause += ' AND '.join(conditions)
    #     sql = 'SELECT "name" FROM {table} WHERE {where_clause}'.format(table=self._table, where_clause=where_clause)
    #     self.env.cr.execute(sql)
    #     names = self.env.cr.fetchall()
    #     if names:
    #         raise ValidationError(_('There is already a "Ordering Restricted" for selected outlet & product within this'
    #                                 ' date range: {cycles}, please check again!').format(
    #             cycles=', '.join([i[0] for i in names])))
    #     return True

    # @api.constrains('product_id', 'outlet_id', 'date_start', 'date_end')
    # def constraint_settings(self):
    #     for r in self:
    #         r._check_date_range()
