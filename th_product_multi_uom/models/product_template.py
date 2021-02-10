# -*- coding: utf-8 -*-
# __author__ = 'trananhdung'

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    multi_uom_ids = fields.One2many(comodel_name='product.multi.uom', inverse_name='product_tmpl_id',
                                    string=_('UOMs'), required=True, copy=True)
    uom_po_id = fields.Many2one('uom.uom', required=False)
    uom_id = fields.Many2one(default=False, required=False)
    barcode = fields.Char(string=_('Barcode (TH Code)'))
    # multi_uom_barcode = fields.Char(string=_('Multi UOM Barcode'), compute='_get_multi_uom_barcode', store=True)

    # @api.depends('multi_uom_ids')
    # def _get_multi_uom_barcode(self):
    #     for product in self:
    #         product.multi_uom_barcode = ','.join(uom.barcode for uom in product.multi_uom_ids if uom and uom.barcode)

    @api.multi
    def get_uom_domain(self, form_type, vendor_id):
        """

        :return:
        """
        self.ensure_one()
        domain = []
        multi_uoms = self.multi_uom_ids
        if vendor_id:
            multi_uoms = multi_uoms.filtered(lambda x: x.vendor_id.id == vendor_id)
        if form_type:
            multi_uoms = multi_uoms.filtered(lambda multi: multi[form_type])

        uom_ids = []
        if multi_uoms:
            uom_ids += multi_uoms.mapped('name').ids
        if not form_type:
            uom_ids += self.uom_id.ids

        return [('id', 'in', uom_ids)]

    @api.constrains('multi_uom_ids', 'uom_id')
    def validate_standard_uom_line(self):
        """
        validate: only allow every product template only have one standard uom in multi uom lines
        :return:
        """
        if self.env.context.get('install_mode'):
            # Do not check constraint during install module
            return True
        standard_line = self.multi_uom_ids.filtered(lambda multi_uom: multi_uom.name.id == self.uom_id.id)
        # Do not raise error for Menu & Combo
        if not standard_line and not self.is_menu_item \
                and not self.is_menu_combo:
            raise ValidationError(
                _('Every product template need have one standard uom line!'))

    @api.constrains('multi_uom_ids')
    def constraint_for_multi_uom(self):
        """

        :return:
        """
        if self.env.context.get('install_mode'):
            # Do not check constraint during install module
            return True
        for r in self:
            if sum([1 if u.is_default else 0 for u in r.multi_uom_ids]) > 1:
                raise ValidationError('Product cannot have more than one default UOM')
            vendor_uoms = {}
            uom_categ_ids = [r.uom_id.category_id.id]
            for u in r.multi_uom_ids:
                uom_categ_ids.append(u.name.category_id.id)
                if u.vendor_id.id in vendor_uoms:
                    vendor_uoms[u.vendor_id.id] |= u
                else:
                    vendor_uoms[u.vendor_id.id] = u
            if len(set(uom_categ_ids)) > 1:
                raise ValidationError(_('System not allow you to select UOMs with different category'))
            for v in vendor_uoms:
                if sum([1 if u.purchase else 0 for u in vendor_uoms[v]]) > 1:
                    raise ValidationError(_('System not allow you to create more than one uom for purchasing'))
                if sum([1 if u.distribution else 0 for u in vendor_uoms[v]]) > 1:
                    raise ValidationError(_('System not allow you to create more than one uom for distribution'))
                if sum([1 if u.storage else 0 for u in vendor_uoms[v]]) > 1:
                    raise ValidationError(_('System not allow you to create more than one uom for storage'))

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        return super(ProductTemplate, self.with_context(PRODUCT_COPY=True)).copy(default)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    barcode = fields.Char(string=_('Barcode (TH Code)'))

    @api.depends('list_price', 'price_extra')
    def _compute_product_lst_price(self):
        """
        I need to override this function from odoo base because I see some issues
        when we create product from dropdown list context value will be {'uom': False}
        then to_uom must be uom.uom() but to_uom = uom.uom(False,) => this is wrong case that odoo not handle
        :return:
        """
        to_uom = None
        # if 'uom' in self._context: # this one not good enough, I need to change such as below
        if self.env.context.get('uom', False):
            to_uom = self.env['uom.uom'].browse(self._context['uom'])

        for product in self:
            if to_uom:
                list_price = product.uom_id._compute_price(product.list_price, to_uom)
            else:
                list_price = product.list_price
            product.lst_price = list_price + product.price_extra

    lst_price = fields.Float(
        compute='_compute_product_lst_price'
    )

    @api.multi
    def get_uom_domain(self, form_type, vendor_id):
        """

        :return:
        """
        self.ensure_one()
        domain = []
        multi_uoms = self.multi_uom_ids
        if vendor_id:
            multi_uoms = multi_uoms.filtered(lambda x: x.vendor_id.id == vendor_id)
        if form_type:
            multi_uoms = multi_uoms.filtered(lambda multi: multi[form_type])

        uom_ids = []
        if multi_uoms:
            uom_ids += multi_uoms.mapped('name').ids
        if not form_type:
            uom_ids += self.uom_id.ids

        return [('id', 'in', uom_ids)]

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        return super(ProductProduct, self.with_context(PRODUCT_COPY=True)).copy(default)
