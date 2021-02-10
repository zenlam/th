# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class ProductMultiUom(models.Model):
    _name = 'product.multi.uom'
    _order = "sequence"

    name = fields.Many2one('uom.uom', string=_('UOM Name'), required=True)
    sequence = fields.Integer(default=1, string=_('Sequence'))
    # uom_type = fields.Selection([
    #     ('bigger', _('Bigger than the reference Unit of Measure')),
    #     ('reference', _('Reference Unit of Measure for this category')),
    #     ('smaller', _('Smaller than the reference Unit of Measure'))],
    #     string=_('UOM Type'), default='reference')
    vendor_id = fields.Many2one(comodel_name='res.partner', domain=[('supplier', '=', True)], string=_('Manufacturer / Brand'))
    factor_inv = fields.Float(string=_('Factor'), default=1.0, digits=0)
    factor = fields.Float(string=_('Real Factor'), default=1.0, digits=0)
    barcode = fields.Char(string=_('Barcode (TH Code)'))
    distribution = fields.Boolean(string=_('Distribution UOM'))
    purchase = fields.Boolean(string=_('Purchase UOM'))
    storage = fields.Boolean(string=_('Storage UOM'))
    outlet_ordering = fields.Boolean(string=_('Outlet Ordering UOM'))
    default_distribution = fields.Boolean(string=_('Default Dist. UOM'))
    product_tmpl_id = fields.Many2one('product.template', string=_('Product Template'))
    description = fields.Char(string=_('Description'))
    is_default = fields.Boolean(default=False)
    active = fields.Boolean(string=_('Active'), default=True)

    _sql_constraints = [
        ('barcode_uniq', 'unique (barcode)', "HAVI Code of UOM already exists !")
    ]

    @api.multi
    @api.constrains('name', 'product_tmpl_id', 'active')
    def constraint_product_multi_uom(self):
        for r in self:
            if r.active:
                other = self.search([('active', '=', True),
                                     ('product_tmpl_id', '=', r.product_tmpl_id.id),
                                     ('name', '=', r.name.id),
                                     ('id', '!=', r.id)])
                if other.ids:
                    raise ValidationError(_('Cannot config same UOM on same product!'))

    @api.multi
    @api.constrains('factor_inv', 'vendor_id', 'product_tmpl_id', 'active')
    def constraint_uom_factor(self):
        for r in self:
            if r.active:
                other = self.search([('active', '=', True),
                                     ('id', '!=', r.id),
                                     ('vendor_id', '=', r.vendor_id.id),
                                     ('product_tmpl_id', '=', r.product_tmpl_id.id),
                                     ('factor_inv', '=', r.factor_inv)])
                if other.ids:
                    raise ValidationError(_('annot config same uom ratio for same vendor on same product!'))

    @api.onchange('default_distribution')
    def onchange_default_dist(self):
        if self.default_distribution:
            self.distribution = True

    @api.onchange('is_default')
    def onchange_is_default(self):
        if self.is_default:
            self.name = self.product_tmpl_id.uom_id.id
            self.factor_inv = 1

    @api.model
    def create(self, vals):
        if 'factor_inv' in vals:
            factor_inv = vals.get('factor_inv')
            vals['factor'] = factor_inv and (1.0 / factor_inv) or 0.0
        if vals.get('barcode'):
            vals['barcode'] = vals['barcode'].strip()
            if self.env.context.get('PRODUCT_COPY', False):
                vals['barcode'] += ' - (copy)'
        res = super(ProductMultiUom, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'factor_inv' in vals:
            factor_inv = vals.get('factor_inv')
            vals['factor'] = factor_inv and (1.0 / factor_inv) or 0.0
        if 'barcode' in vals and vals['barcode'] is True:
            vals['barcode'] = vals['barcode'].strip()
        res = super(ProductMultiUom, self).write(vals)
        return res

    @api.constrains('is_default')
    def validate_standard_uom_line(self):
        """
        validate: only allow every product template only have one standard uom in multi uom lines
        :return:
        """
        for multi_uom in self:
            if multi_uom.is_default:
                result = self.search(
                    [('product_tmpl_id', '=', multi_uom.product_tmpl_id.id), ('id', '!=', multi_uom.id),
                     ('is_default', '=', True)], limit=1)
                if result:
                    raise ValidationError(_('Every product template only have one standard uom line!'))

    @api.constrains('purchase', 'storage', 'distribution', 'is_default', 'outlet_ordering')
    def constraint_uom_type(self):
        """
        If any user add the line to configured UOM, then at lease user have to select either
        Purchase UOM, Storage UOM or Distribution UOM for this added UOM. Do not allowed to
        save with tic any one of the UOM. If "Is Default UOM" is tic then allowed to save without
         select either Purchase UOM, Storage UOM or Distribution UOM
        :return:
        """
        for r in self:
            if not (r.is_default or r.storage or r.distribution or r.purchase or r.outlet_ordering):
                raise ValidationError(_('UOM must be either Purchase UOM, Storage UOM, Outlet Ordering UOM or '
                                        'Distribution UOM if that UOM is not default UOM'))

    # Change to use SQL constraint
    # @api.constrains('name')
    # def validate_uom(self):
    #     """
    #     validate: don't allow duplicate uom in every product template
    #     :return:
    #     """
    #     for multi_uom in self:
    #         result = self.search([('product_tmpl_id', '=', multi_uom.product_tmpl_id.id),
    #                               ('name', '=', self.name.id),
    #                               ('vendor_id', '=', multi_uom.vendor_id.id),
    #                               ('id', '!=', multi_uom.id)], limit=1)
    #         if result:
    #             raise ValidationError(_('Duplicate UOM name!'))

    @api.multi
    def button_deactivate(self):
        """
        Archive uom
        :return:
        """
        self.write({'active': False})

    @api.multi
    def button_activate(self):
        """
        active UOM
        :return:
        """
        self.write({'active': True})
    
    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if 'barcode' not in default:
            default.update(barcode=self.barcode + ' - (copy)')
        return super(ProductMultiUom, self).copy(default)

