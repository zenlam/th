# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class OutletOrderingTemplate(models.Model):
    _name = 'outlet.ordering.template'
    _description = _('Outlet Ordering Template')
    _inherit = ['mail.thread']

    name = fields.Char(string=_('Name'), required=True)
    # vendor_id = fields.Many2one(comodel_name='res.partner', string=_('Vendor'), required=True)
    date_start = fields.Date(string=_('Start Date Validity'))
    date_end = fields.Date(string=_('End Date Validity'))
    product_ids = fields.One2many(comodel_name='outlet.ordering.template.product', inverse_name='template_id', string=_('Products'))

    _sql_constraints = [
        ('date_range_check', 'check (date_start <= date_end)',
         _('End date cannot earlier than start date')),
    ]

    @api.multi
    @api.constrains('product_ids')
    def constraint_products(self):
        for r in self:
            selected_products = []
            for p in r.product_ids:
                if p.product_id.id not in selected_products:
                    selected_products.append(p.product_id.id)
                else:
                    raise ValidationError(_('Duplicate product %s') % p.product_id.name)


class OutletOrderingTemplateProduct(models.Model):
    _name = 'outlet.ordering.template.product'

    @api.multi
    @api.depends('product_id.deny_outlet_ids.outlet_id')
    def _compute_restricted_outlet(self):
        for r in self:
            r.deny_outlet_ids = r.product_id.deny_outlet_ids.mapped('outlet_id')

    product_id = fields.Many2one(comodel_name='product.product', string=_('Product'), required=True)
    product_uom = fields.Many2one(comodel_name='uom.uom', string=_('Ordering UOM'), required=False)
    outlet_ids = fields.Many2many(comodel_name='stock.warehouse', relation='ordering_template_outlet_rel',
                                  column1='template_id', column2='outlet_id',
                                  domain=[('create_from', '=', 'outlet')])
    deny_outlet_ids = fields.Many2many(comodel_name='stock.warehouse',
                                       compute='_compute_restricted_outlet',
                                       store=True,
                                       relation='ordering_template_outlet_deny_rel',
                                       column1='ordering_tmpl_line_id',
                                       column2='outlet_id')
    area_id = fields.Many2one(comodel_name='res.country.area', string='Outlet based on Area')
    date_start = fields.Date(string=_('Start Date Validity'), related='template_id.date_start')
    date_end = fields.Date(string=_('End Date Validity'), related='template_id.date_end')
    template_id = fields.Many2one(comodel_name='outlet.ordering.template', string='Template')
    history_template_id = fields.Many2one(comodel_name='outlet.ordering.history.template',
                                          # relation='outlet_ordering_template_product_history_rel',
                                          # column1='tmpl_product_id', column2='history_id',
                                          string=_('Sales Template History'))

    @api.multi
    @api.constrains('outlet_ids', 'area_id')
    def constraint_outlet_and_area(self):
        for r in self:
            if r.outlet_ids.ids and r.area_id.id:
                raise ValidationError(_('You only can fill either "Outlet(s)" or "Outlet based on Area" '
                                        'for Ordering Template Products'))

    @api.onchange('outlet_ids')
    def onchange_outlets(self):
        if self.outlet_ids.ids:
            self.area_id = False
            if self.outlet_ids.ids[-1] in self.deny_outlet_ids.ids:
                return {'warning': {'title': _('Warning'),
                                    'message': _('You have just selected a restricted outlet (%s)') % self.outlet_ids[-1].name}}

    @api.onchange('area_id')
    def onchange_area_id(self):
        if self.area_id.id:
            self.outlet_ids = [(5, 0, 0)]
