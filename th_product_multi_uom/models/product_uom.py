# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError, ValidationError


class ProductUom(models.Model):
    _inherit = 'uom.uom'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []

        # set domain filter for uom - get by multi uom config in product template
        product_tmpl_id = self._context.get('product_tmpl_id', False)
        product_id = self._context.get('product_id', False)
        form_type = self._context.get('type', False)
        product_tmpl = None

        if product_tmpl_id:
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
        elif product_id:
            product = self.env['product.product'].browse(product_id)
            product_tmpl = product.product_tmpl_id

        if product_tmpl:
            list_uom = set()
            index = -1
            # get old list id if exist in domain
            for i in range(0, len(args)):
                arg = args[i]
                if arg[0] == 'id' and arg[1] == 'in':
                    list_uom = set(arg[2])
                    index = i
            # get list id uom by uom tab on product form
            for uom_line in self._get_multi_uom_by_product(product_tmpl, form_type):
                list_uom |= {uom_line.name.id}
            # append uom_id from uom_id of product form (standard uom)
            list_uom |= {product_tmpl.uom_id.id}
            if len(list_uom) > 0:
                # add new domain 'id in []' if not exist
                if index == -1:
                    args.append(('id', 'in', list(list_uom)))
                else:
                    # override domain 'id in []' if exist
                    args.remove(args[index])
                    args.append(('id', 'in', list(list_uom)))
        return super(ProductUom, self).name_search(name, args, operator, limit)

    def _get_multi_uom_by_product(self, product, form_type):
        """
        filter list multi uom from product by 'purchse', 'selling', 'distribution'
        :param product: product template object
        :param form_type: 'purchase' or 'selling' or 'distribution'
        :return:
        """
        if form_type:
            return product.multi_uom_ids.filtered(
                lambda multi: multi[form_type])
        else:
            return product.multi_uom_ids

    @api.model
    def _prepare_domain_before_search(self, domain=None):
        """

        :param domain:
        :return:
        """
        product_id = self.env.context.get('restrict_uom_on_product', False)
        form_type = self._context.get('type', False)
        vendor_id = self._context.get('vendor_id', False)
        if product_id:
            product_model = 'product.product'
            if self.env.context.get('is_template', False):
                product_model = 'product.template'
            product = self.env[product_model].browse(product_id)

            domain.append(product.get_uom_domain(form_type, vendor_id)[0])
            return domain
        else:
            return domain

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """

        :param args:
        :param offset:
        :param limit:
        :param order:
        :param count:
        :param access_rights_uid:
        :return:
        """
        if args is None:
            args = []
        self._prepare_domain_before_search(args)
        return super(ProductUom, self)._search(
            args, offset, limit, order, count, access_rights_uid
        )

    @api.multi
    def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP'):
        res = super(ProductUom, self)._compute_quantity(
            qty, to_unit, round=round, rounding_method=rounding_method)

        # re-calculate qty by factor of multi uom config on product form
        product_tmpl_id = self._context.get('product_tmpl_id')
        if product_tmpl_id:
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            from_multi_uom = self.env['product.multi.uom'].search(
                    [('name', '=', self.id), ('product_tmpl_id', '=', product_tmpl.id)], limit=1)
            if from_multi_uom.factor:
                amount = qty / from_multi_uom.factor
                if to_unit:
                    to_multi_uom = self.env['product.multi.uom'].search(
                        [('name', '=', to_unit.id), ('product_tmpl_id', '=', product_tmpl.id)], limit=1)

                    if to_multi_uom:
                        amount = amount * to_multi_uom.factor
                        if round:
                            amount = tools.float_round(amount, precision_rounding=to_unit.rounding,
                                                       rounding_method=rounding_method)
                        return amount
        return res

    # NOTE : odoo base _compute price use the base uom factor to calculate now we use multi uom if found else same as base
    @api.multi
    def _compute_price(self, price, to_unit):
        amount = super(ProductUom, self)._compute_price(price, to_unit)
        self.ensure_one()
        product_tmpl_id = self._context.get('product_tmpl_id')
        if product_tmpl_id:
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            from_multi_uom = self.env['product.multi.uom'].search(
                [('name', '=', self.id), ('product_tmpl_id', '=', product_tmpl.id)], limit=1)

            to_multi_uom = self.env['product.multi.uom'].search(
                [('name', '=', to_unit.id), ('product_tmpl_id', '=', product_tmpl.id)], limit=1)

            if not self or not price or not to_unit or self == to_unit:
                return price
            if self.category_id.id != to_unit.category_id.id:
                return price

            if from_multi_uom and  to_multi_uom:
                amount = price * from_multi_uom.factor
                if to_multi_uom:
                    amount = amount / to_multi_uom.factor
        return amount

    @api.constrains('category_id', 'uom_type', 'active')
    def _check_category_reference_uniqueness(self):
        """ Force the existence of only one UoM reference per category
            NOTE: this is a constraint on the all table. This might not be a good practice, but this is
            not possible to do it in SQL directly.
        """
        # NOTE: simply ignore this constrain as we do not require this constrain for Tim Hortons
        if False:
            return super(ProductUom, self)._check_category_reference_uniqueness()
