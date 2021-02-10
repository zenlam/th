# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class Uom(models.Model):
    _inherit = 'uom.uom'

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
        ordering_product_id = self.env.context.get('product_ordering_uom', False)
        if ordering_product_id:
            uoms = self.env['product.product'].browse(ordering_product_id).multi_uom_ids.filtered(lambda x: x.outlet_ordering)
            args.append(('id', 'in', uoms.mapped('name').ids))
        return super(Uom, self)._search(args, offset, limit, order, count, access_rights_uid)
