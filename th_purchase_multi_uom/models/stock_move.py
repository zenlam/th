from odoo import models, fields, api
from odoo.tools.translate import _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                price_unit = \
                line.taxes_id.with_context(round=False).compute_all(price_unit,
                                                                    currency=line.order_id.currency_id,
                                                                    quantity=1.0)[
                    'total_excluded']
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
        return super(StockMove, self)._get_price_unit()

    # NOTE: Over-write whole onchange method, however this field is readonly for now.
    # Handle Multi UOM if in future needs to make this field editable again.
    @api.onchange('product_uom')
    def onchange_product_uom(self):
        multi_uom_obj = self.env['product.multi.uom']
        new_product_uom = multi_uom_obj.search(
            [('name', '=', self.product_uom.id),
             ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)], limit=1)
        product_base_uom = multi_uom_obj.search(
            [('name', '=', self.product_id.uom_id.id),
             ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)], limit=1)

        if (not new_product_uom) and (not product_base_uom):
            new_product_uom = self.product_uom
            product_base_uom = self.product_id.uom_id

        # bellow is the odoo base condition just keep for ref.
        # if self.product_uom.factor > self.product_id.uom_id.factor:
        if new_product_uom.factor > product_base_uom.factor:
            return {
                'warning': {
                    'title': "Unsafe unit of measure",
                    'message': _("You are using a unit of measure smaller than the one you are using in "
                                 "order to stock your product. This can lead to rounding problem on reserved quantity. "
                                 "You should use the smaller unit of measure possible in order to valuate your stock or "
                                 "change its rounding precision to a smaller value (example: 0.00001)."),
                }
            }
