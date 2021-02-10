# __author__ = 'minhld'

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools.float_utils import float_is_zero, float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _get_stock_move_price_unit(self):
        """
        re-calculate price_unit by todo_uom factor
        :return:
        """
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0,
                product=line.product_id, partner=line.order_id.partner_id
            )['total_excluded']
        # get price unit by factor of multi uom
        if line.product_uom.id != line.product_id.uom_id.id:
            multi_uom_obj = self.env['product.multi.uom']
            product_tmpl_id = line.product_id.product_tmpl_id.id

            from_multi_uom = multi_uom_obj.search(
                [('name', '=', line.product_id.uom_id.id),
                 ('product_tmpl_id', '=', product_tmpl_id)], limit=1)
            to_multi_uom = multi_uom_obj.search(
                [('name', '=', line.product_uom.id),
                 ('product_tmpl_id', '=', product_tmpl_id)], limit=1)

            price_unit *= to_multi_uom.factor / from_multi_uom.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id.compute(price_unit,
                                                   order.company_id.currency_id,
                                                   round=False)
        return price_unit

    # NOTE this one to get the correct received qty based on MULTI UOM
    def _update_received_qty(self):
        for line in self:
            super(PurchaseOrderLine,
                  line.with_context(product_tmpl_id=line.product_id.product_tmpl_id.id))._update_received_qty()
