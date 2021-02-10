from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ScrapPickingLine(models.Model):
    _name = 'scrap.picking.line'
    _description = 'TH Scrap Picking Line'

    menu_id = fields.Many2one('product.product', string='Menu',
                              domain=[('is_menu_item', '=', True)])
    ingredient_id = fields.Many2one('product.product', string='Ingredients',
                                    domain=[('is_menu_item', '=', False)])
    quantity = fields.Float(string='Quantity', default=1)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    scrap_picking_id = fields.Many2one('scrap.picking')

    @api.model
    def write(self, vals):
        res = super(ScrapPickingLine, self).write(vals)
        if not self.menu_id and not self.ingredient_id:
            raise ValidationError(_('Please configure either menu or '
                                    'ingredient'))
        return res

    @api.model
    def create(self, vals):
        if vals['menu_id'] is False and vals['ingredient_id'] is False:
            raise ValidationError(_('Please configure either menu or '
                                    'ingredient'))
        return super(ScrapPickingLine, self).create(vals)

    @api.onchange('menu_id', 'ingredient_id')
    def onchange_menu_ingredient(self):
        if self.menu_id and self.ingredient_id:
            raise ValidationError(_('Cannot configure both menu and ingredient'
                                    ' in one line'))
        if self.menu_id:
            self.product_uom = self.menu_id.uom_id.id
        elif self.ingredient_id:
            self.product_uom = self.ingredient_id.uom_id.id
