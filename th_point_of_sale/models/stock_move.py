# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    before_consolidate_price_unit = fields.Float('Before Consolidate Unit Price')
    while_consolidate_outlet_price_unit = fields.Float('while consolidate Unit Price')

    @api.multi
    def write(self, vals):

        if 'is_pos_picking' in self.env.context.keys() and self.env.context['is_pos_picking'] and 'price_unit' in vals.keys():
            for move in self:
                print("while_consolidate_outlet_price_unit --------- ",move.while_consolidate_outlet_price_unit)
                price_value =  vals['value'] if 'value' in vals.keys() else move.value
                if vals['price_unit'] > 0:
                    vals['before_consolidate_price_unit'] = vals['price_unit']
                    vals['value'] = move.while_consolidate_outlet_price_unit * (price_value / vals['before_consolidate_price_unit'])
                    vals['price_unit'] = move.while_consolidate_outlet_price_unit
                elif vals['price_unit'] < 0:
                    vals['before_consolidate_price_unit'] = vals['price_unit']
                    vals['value'] = (move.while_consolidate_outlet_price_unit * -1 ) * (
                                price_value / vals['before_consolidate_price_unit'])
                    vals['price_unit'] = move.while_consolidate_outlet_price_unit * -1
                else: # write else case just to be safe normally price_unit won't be zero.
                    vals['before_consolidate_price_unit'] = vals['price_unit']
                    vals['value'] = move.while_consolidate_outlet_price_unit
                    vals['price_unit'] = move.while_consolidate_outlet_price_unit
                print("--------move write vals",move, vals)

                super(StockMove, move).write(vals)
            return True
        else:
            return super(StockMove, self).write(vals)

