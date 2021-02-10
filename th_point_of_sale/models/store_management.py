from odoo import api, fields, models, _
from odoo.exceptions import Warning


class OutletManagement(models.Model):
    _inherit = 'stock.warehouse'

    top_selling_menu_ids = fields.Many2many(
        'product.product', 'top_selling_menu_outlet_rel',
        'outlet_id', 'menu_id', string='Top Selling Menus',
        domain=[('is_menu_item', '=', True), ('is_menu_combo', '=', False)])

    @api.multi
    def write(self, vals):
        res = super(OutletManagement, self).write(vals)
        for outlet in self:
            if outlet.top_selling_menu_ids and len(outlet.top_selling_menu_ids) > 4:
                raise Warning(_('You can only set up to 4 top selling menus '
                                'per Outlet.'))
        return res
