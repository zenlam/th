from itertools import combinations

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    @api.constrains('item_ids')
    def _check_item_ids(self):
        check_dates = []
        overlapped_dates = []
        combo_of_pricelist_items = {}
        for item_id in self.item_ids:
            if item_id.date_start > item_id.date_end:
                check_dates.append(item_id)
            if item_id.name in combo_of_pricelist_items:
                combo_of_pricelist_items[item_id.name].append(
                    (item_id.date_end, item_id.date_start))
            else:
                combo_of_pricelist_items[item_id.name] = [
                    (item_id.date_end, item_id.date_start)]
        for key, val in combo_of_pricelist_items.items():
            if len(val) > 1:
                all_combination = combinations(val, 2)
                for combi in list(all_combination):
                    #
                    # combi = [(date_end_1, date_start_1),
                    #          (date_end_2, date_start_2)]
                    #
                    # overlapped = min(date_end_1 - date_start_2,
                    #                  date_end_2 - date_start_1).days + 1
                    #
                    overlapped = min(combi[0][0] - combi[1][1],
                                     combi[1][0] - combi[0][1]).days + 1
                    if overlapped > 0:
                        overlapped_dates.append(key)
        warning_msg = ''
        if check_dates:
            warning_msg += 'The start date must be ' \
                           'anterior to the end date. ' \
                           '\nPlease, refer following items: %s\n\n' % \
                           ",".join([x.name for x in check_dates])

        if overlapped_dates:
            if warning_msg:
                warning_msg += '----------------------' \
                               '---------------------' \
                               '---------------------' \
                               '----------------------\n\n'
            warning_msg += 'Multiple pricelist-items defines ' \
                           'for following items: %s , ' \
                           '\nAnd the duration(start date, end date) are ' \
                           'overlapped with each other.' % \
                           ",".join([x for x in overlapped_dates])
        if warning_msg:
            raise ValidationError(_(warning_msg))


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    # Add options like...
    #   4_pos_menu -> Menu
    applied_on = fields.Selection(selection_add=[('4_pos_menu', 'Menu')],
                                  default='4_pos_menu')
    min_quantity = fields.Integer(default=1)
    time_range_ids = fields.Many2many('th.time.range',
                                      'time_range_pricelist_item_rel',
                                      'col1', 'col2', 'Time Range',
                                      help='If empty then menu is '
                                           'available whole day!')

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        super(PricelistItem, self)._onchange_applied_on()
        res = {'domain': {'product_id': []}}
        if self.applied_on != '4_pos_menu':
            self.product_id = False
        if self.applied_on == '4_pos_menu':
            self.compute_price = 'fixed'
            res['domain']['product_id'] = [('is_menu_item', '=', True)]
        return res

    # @todo Siddharth Bhalgami
    # Need to check the strange behavior of onchange on wizard
    #
    # @api.onchange('date_start', 'date_end')
    # def _onchange_on_dates(self):
    #     if self.date_start and self.date_end and \
    #             (self.date_start > self.date_end):
    #         raise UserError(_('The start date must be '
    #                           'anterior to the end date.'))
