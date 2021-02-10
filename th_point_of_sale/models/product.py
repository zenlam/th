from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, Warning


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_menu_item = fields.Boolean('Is Menu Item?')
    is_menu_combo = fields.Boolean('Combo Menu')
    menu_categ_id = fields.Many2one('th.menu.category',
                                    'Report Analysis Category')
    modifier_group_id = fields.Many2one('th.modifier.group',
                                        'Modifier Group')
    void_require_approval = fields.Boolean('Void Require Approval')
    recovery = fields.Float('Recovery (%)', required=True)
    # m_extra_price = fields.Float('Extra Price',
    #                              digits=dp.get_precision('Product Price'),
    #                              default=0.0)
    # m_weight = fields.Integer('Modifier Weight', default=1)
    output_tax_conf = fields.Boolean(related="company_id.output_tax_conf",
                                     store=True)
    smart_select_id = fields.Many2one('th.smart.select', 'Smart Select',
                                      readonly=True)

    @api.constrains('multi_uom_ids', 'uom_id')
    def validate_standard_uom_line(self):
        # Do not raise error for Menu & Combo
        if not self.is_menu_item and not self.is_menu_combo:
            return super(ProductTemplate, self).validate_standard_uom_line()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_ingredient_ids = fields.Many2many(
        'th.ingredient.product', 'product_ingredient_rel', 'col1', 'col2',
        'Ingredients')
    combo_menu_ids = fields.Many2many(
        'th.menu.product', 'prod_combo_menu_rel', 'col1', 'col2', 'Menus')
    special_modifier_ids = fields.One2many(
        'th.special.modifier.options', 'menu_id', string='Special Modifiers')
    primary_menu_in_combo_ids = fields.Many2many(
        'product.product', 'combo_primary_menu_rel', 'col1', 'col2',
        'Primary Product in Combo', readonly=True)

    # Inherit due to Special Modifiers which shows only basic ingredients
    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        if self.env.context.get('special_modifier_option') and \
                self.env.context.get('menu_id'):
            ingredient_ids = []
            menu = self.browse(self.env.context.get('menu_id'))
            for ingredient in menu.product_ingredient_ids:
                ingredient_ids.append(ingredient.product_id.id)
            args += [('id', 'in', ingredient_ids)]
        return super(ProductProduct, self)._name_search(
            name=name, args=args, operator=operator,
            limit=limit, name_get_uid=name_get_uid)

    @api.multi
    def write(self, values):
        # FIXME.. Proper way to implement the logic for
        #  `primary_menu_in_combo_ids`
        old_combo_menus = []
        for prod in self:
            old_combo_menus.append({prod.id: prod.combo_menu_ids})

        res = super(ProductProduct, self).write(values)
        for prod in self:
            if prod.is_menu_combo:
                default_menus = [menu.product_id
                                 for menu in prod.combo_menu_ids
                                 if menu.default_menu_for_combo]

                if not default_menus:
                    raise ValidationError(_('There is no default menu set '
                                            'for active combo.'))
                if len(default_menus) > 1:
                    raise ValidationError(_('You can not set multiple menus '
                                            'as default Menu for '
                                            'active combo.'))

                # After above condition default_menus contains only
                # single product
                default_menus[0].write({
                    'primary_menu_in_combo_ids': [(4, prod.id)]
                })

                # Difference between old & new is always single record
                for old_data in old_combo_menus:
                    for key, val in old_data.items():
                        if key == prod.id:
                            for menu_prod in (val - prod.combo_menu_ids):
                                if menu_prod.default_menu_for_combo:
                                    menu_prod.product_id.write({
                                        'primary_menu_in_combo_ids':
                                            [(3, prod.id)]
                                    })
        return res

    @api.multi
    def unlink(self):
        for product in self:
            if product.pricelist_item_ids:
                raise Warning(_("Can not delete menu(s), "
                                "as it's already used inside Pricelist(s)."))
        return super(ProductProduct, self).unlink()
