# __author__ = 'trananhdung'

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    name = fields.Char(default=False)
    is_hq = fields.Boolean(default=False, string=_('Is Head Quarter'))
    default_resupply = fields.Boolean(default=False, string=_('Default Resupply'))

    @api.constrains('is_hq')
    def _check_duplicate_is_hq(self):
        all_wh = self.search([
            ('is_hq', '=', True),
            ('active', '=', self.active),
            ('company_id', '=', self.company_id.id),
            ('id', '!=', self.id)])
        if all_wh:
            raise ValidationError(_('%s is already configured as IS HQ Warehouse, User cannot configured multiple warehouse as a HQ Warehouse !')%(all_wh[0].name))

    # def _get_outlet_id(self):
    #     for warehouse in self:
    #         store = self.env['stock.warehouse'].search([('warehouse_id', '=', warehouse.id)], limit=1)
    #         warehouse.outlet_id = store.id
    #
    # @api.multi
    # def search_outlet_id(self, operator, value):
    #     warehouse_ids = self.env['stock.warehouse']
    #     if value:
    #         if type(value) == str:
    #             store = self.env['stock.warehouse'].search([('name', operator, value)])
    #         else:
    #             store = self.env['stock.warehouse'].search(
    #                 [('id', operator, value)])
    #         warehouse_ids = store.mapped('warehouse_id')
    #
    #     return [('id', 'in', warehouse_ids.ids)]
