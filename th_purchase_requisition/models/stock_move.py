# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = "stock.move"

    outlet_std_price_unit = fields.Float(
        string=_('Outlet Standard Cost'), digits=dp.get_precision('Product Price'),
        help=_('Standard Outlet Cost of the product, in the default UOM of the product.'),
        default=0.0,
    )

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id):
        # This method returns a dictonary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
        self.ensure_one()
        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
                                                                     debit_account_id, credit_account_id)

        # NOTE this logic is applied only if the Picking is generated from PR
        if self.picking_id and self.picking_id.purchase_request_id and self.outlet_std_price_unit != debit_value:
            hq_warehouse = self.env['stock.warehouse'].search([('is_hq', '=', True)], limit=1)
            if not hq_warehouse:
                raise ValidationError("Missing Head Quarter warehouse in the system !")
            diff_hq_bare = debit_value - (self.outlet_std_price_unit * qty)
            if diff_hq_bare > 0:
                # if difference is more then 0
                # Step : 1  need to reduce difference from original debit line credit/debit amount
                if debit_value > 0:
                    rslt['debit_line_vals']['debit'] = rslt['debit_line_vals']['debit'] - abs(diff_hq_bare)
                else:
                    rslt['debit_line_vals']['credit'] = rslt['debit_line_vals']['credit'] - abs(diff_hq_bare)
                # Step : 2  need to generate new debit line with difference amount which bare by head quarter (use HQ analytic account)
                rslt['hq_debit_line_vals'] = rslt['debit_line_vals'].copy() # copy whole line and then update debit value
                rslt['hq_debit_line_vals']['analytic_account_id'] = hq_warehouse.analytic_account_id.id
                if debit_value > 0:
                    rslt['hq_debit_line_vals']['debit'] =  abs(diff_hq_bare)
                else:
                    rslt['hq_debit_line_vals']['credit'] = abs(diff_hq_bare)
            else:
                # if difference is less then 0
                # Step : 1  need to add difference to original debit line credit/debit amount
                if debit_value > 0:
                    rslt['debit_line_vals']['debit'] = rslt['debit_line_vals']['debit'] + abs(diff_hq_bare)
                else:
                    rslt['debit_line_vals']['credit'] = rslt['debit_line_vals']['credit'] + abs(diff_hq_bare)

                # if negative then generate new move line with credit difference amount
                rslt['hq_debit_line_vals'] = rslt['debit_line_vals'].copy()  # copy whole line and then update debit value
                rslt['hq_debit_line_vals']['debit'] = 0
                rslt['hq_debit_line_vals']['credit'] = abs(diff_hq_bare)
                rslt['hq_debit_line_vals']['analytic_account_id'] = hq_warehouse.analytic_account_id.id

            if self.purchase_line_id and diff_hq_bare > 0:
                purchase_currency = self.purchase_line_id.currency_id
                if purchase_currency != self.company_id.currency_id:
                    # Do not use price_unit since we want the price tax excluded. And by the way, qty
                    # is in the UOM of the product, not the UOM of the PO line.
                    purchase_price_unit = (
                        self.purchase_line_id.price_subtotal / self.purchase_line_id.product_uom_qty
                        if self.purchase_line_id.product_uom_qty
                        else self.purchase_line_id.price_unit
                    )
                    currency_move_valuation = purchase_currency.round(purchase_price_unit * abs(qty))
                    rslt['hq_debit_line_vals']['amount_currency'] = rslt['hq_debit_line_vals'][
                                                                      'credit'] and -currency_move_valuation or currency_move_valuation
                    rslt['hq_debit_line_vals']['currency_id'] = purchase_currency.id

        return rslt
