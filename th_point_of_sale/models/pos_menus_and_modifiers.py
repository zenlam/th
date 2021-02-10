from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class ThSpecialModifierOptions(models.Model):
    _name = 'th.special.modifier.options'
    _description = 'Th Special Modifier Options'
    _rec_name = 'modifier_option_id'

    menu_id = fields.Many2one('product.product', 'Menu Item')
    modifier_option_id = fields.Many2one(
        'th.modifier.options', 'Special Modifier Option',
        required=True, domain=[('special_modifier', '=', True)])
    modifier_product_ids = fields.One2many('th.modifier.product',
                                           'special_modifier_id',
                                           'Special Ingredients')
    font_color = fields.Char('Font Color')
    background_color = fields.Char('Background Color')

    @api.multi
    def special_modifier_conf(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'th.special.modifier.options',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'th_point_of_sale.th_special_modifier_options_form_view').id,
            'context': {'special_modifier_conf': True},
            'target': 'new',
        }


class ThMenuUpSell(models.Model):
    _name = 'th.menu.upsell'
    _description = 'TH Menu UpSell'
    _rec_name = 'pos_categ_id'

    th_menu_id = fields.Many2one('th.menu.product', 'Menu')
    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of menu categories.")
    pos_categ_id = fields.Many2one('pos.category', 'Menu Category',
                                   required=True)
    auto_compute_surcharge = fields.Boolean('Auto Compute Surcharge')
    fixed_surcharge = fields.Float('Fixed Surcharge', digits=0)
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')

    @api.onchange('auto_compute_surcharge')
    def onchange_auto_compute_surcharge(self):
        if self.auto_compute_surcharge:
            self.fixed_surcharge = 0.0


class ThMenuProduct(models.Model):
    _name = 'th.menu.product'
    _description = 'TH Menu Product'
    _rec_name = 'product_id'

    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of menu categories.")
    pos_categ_id = fields.Many2one('pos.category', 'Menu Category')
    default_menu_for_combo = fields.Boolean("Default Menu")
    product_id = fields.Many2one('product.product', 'Menu',
                                 domain=[('is_menu_item', '=', True),
                                         ('is_menu_combo', '=', False)])
    min_selection = fields.Integer('Min', default=1)
    max_selection = fields.Integer('Max', default=1)
    allow_substitution = fields.Boolean('Allow Substitution')
    cheaper_substitution = fields.Boolean('Cheaper Substitution')
    auto_compute_surcharge = fields.Boolean('Auto Compute Surcharge')
    fixed_surcharge = fields.Float('Fixed Surcharge', digits=0)
    menu_upsell_ids = fields.One2many('th.menu.upsell',
                                      'th_menu_id',
                                      'Upsell Config')

    @api.onchange('default_menu_for_combo')
    def onchange_default_meu_for_combo(self):
        if self.default_menu_for_combo:
            self.pos_categ_id = False
            self.allow_substitution = False
            self.cheaper_substitution = False
            self.auto_compute_surcharge = False
            self.fixed_surcharge = False

    @api.onchange('auto_compute_surcharge')
    def onchange_auto_compute_surcharge(self):
        if self.auto_compute_surcharge:
            self.fixed_surcharge = 0.0

    @api.multi
    def action_menu_upsell(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'th.menu.product',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'th_point_of_sale.th_menu_product_upsell_form_view').id,
            'target': 'new',
        }


class ThIngredientProduct(models.Model):
    _name = 'th.ingredient.product'
    _description = 'TH Ingredient Product'
    _rec_name = 'product_id'

    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of menu categories.")
    product_id = fields.Many2one('product.product', 'Product',
                                 domain=[('is_menu_item', '=', False),
                                         ('is_menu_combo', '=', False)],
                                 required=True)
    qty = fields.Float('Quantity', default=1.0, required=True)
    recovery = fields.Float('Recovery (%)', required=True)
    inv_deduction_qty = fields.Float(compute='_get_inventory_deduction_qty',
                                     string='Inventory Deduction Quantity')
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id',
                             readonly=True)
    optional = fields.Boolean('Optional')
    show_in_cart = fields.Boolean('Show in Cart')
    modifier_group_ids = fields.Many2many('th.modifier.group',
                                          'ingredient_modifier_grps',
                                          'ingredient_id',
                                          'modifier_id',
                                          'Modifier Groups')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.recovery = self.product_id.product_tmpl_id.recovery

    @api.depends('qty', 'recovery')
    def _get_inventory_deduction_qty(self):
        for rec in self:
            if rec.qty and rec.recovery:
                rec.inv_deduction_qty = rec.qty / (rec.recovery / 100)

    @api.onchange('optional')
    def _onchange_optional(self):
        if self.optional:
            self.modifier_group_ids = \
                [(6, 0,
                  self.product_id.product_tmpl_id.modifier_group_id.ids)] \
                if self.product_id.product_tmpl_id.modifier_group_id else False
        else:
            self.modifier_group_ids = False


class ThModifierOptions(models.Model):
    _name = 'th.modifier.options'
    _description = 'TH Modifier Options'
    _order = 'sequence desc'

    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of menu categories.")
    name = fields.Char('Name', index=True, required=True, translate=True)
    description = fields.Char('Description', required=True)
    is_basic = fields.Boolean('Basic Option')
    remove_extra = fields.Boolean('Remove Extra')
    special_modifier = fields.Boolean('Special Modifier')
    qty_multiplier = fields.Float('Qty Multiplier', required=True)
    price_multiplier = fields.Float('Price Multiplier', required=True)

    _sql_constraints = [('th_modifier_options_name_unique', 'unique(name)',
                         'Modifier Option with same name is '
                         'already exists.')]

    @api.multi
    def write(self, vals):
        for opt in self:
            if opt.is_basic:
                raise UserError(
                    _('This is basic modifier option, You cannot amend this.'))
        return super(ThModifierOptions, self).write(vals)

    @api.multi
    def unlink(self):
        for opt in self:
            if opt.is_basic:
                raise UserError(
                    _('You cannot delete basic option - (%s)' % opt.name))
        return super(ThModifierOptions, self).unlink()


class ThModifierProduct(models.Model):
    _name = 'th.modifier.product'
    _description = 'TH Modifier Product'
    _inherit = 'th.ingredient.product'
    _rec_name = 'product_id'

    modifier_id = fields.Many2one('th.modifier.group', 'Modifier Category')
    special_modifier_id = fields.Many2one('th.special.modifier.options', 'Special Modifier Option')
    font_color = fields.Char('Font Color')
    background_color = fields.Char('Background Color')
    code_name = fields.Char('Code Name', size=4, required=True,
                            help='Which shows in pos screen instead '
                                 'of full name.')
    # weight = fields.Integer('Weight', default=1)
    qty_multiplier = fields.Float('Qty Multiplier')
    extra_price = fields.Float('Extra Price',
                               digits=dp.get_precision('Product Price'),
                               default=0.0)
    max_selection_qty = fields.Integer('Max Selection Qty', default=1)

    @api.model_create_multi
    def create(self, vals):
        m_products = super(ThModifierProduct, self).create(vals)
        for res in m_products:
            res.product_id.modifier_group_id = res.modifier_id.id
            # res.product_id.m_weight = res.weight
            # res.product_id.m_extra_price = res.extra_price
        return m_products

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(ThModifierProduct, self)._onchange_product_id()
        if self.env.context.get('special_modifier_conf'):
            menu = self.special_modifier_id.menu_id
            if menu and self.product_id:
                for ingredient in menu.product_ingredient_ids:
                    if self.product_id == ingredient.product_id:
                        self.recovery = ingredient.recovery
                        self.qty = ingredient.qty

    @api.onchange('qty_multiplier')
    def _onchange_qty_multiplier(self):
        if self.qty_multiplier and \
                self.env.context.get('special_modifier_conf'):
            menu = self.special_modifier_id.menu_id
            if menu and self.product_id:
                for ingredient in menu.product_ingredient_ids:
                    if self.product_id == ingredient.product_id:
                        self.qty = (ingredient.qty * self.qty_multiplier) - \
                                   ingredient.qty


class ThModifierGroup(models.Model):
    _name = 'th.modifier.group'
    _description = 'TH Modifier Group'

    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of menu categories.")
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', index=True, required=True, translate=True)
    product_option_ids = fields.One2many('th.modifier.product', 'modifier_id',
                                         string='Ingredient Options')
    modifier_option_ids = fields.Many2many(
        'th.modifier.options', 'category_modifier_table',
        'rec1', 'rec2', string='Modifier Option',
        domain=[('special_modifier', '=', False)])
    display_on_receipt = fields.Boolean("Display on Receipt")
    allow_multiple_selection = fields.Boolean("Allow Multiple Selection?")
    max_selection = fields.Integer("Max Selection")
    font_color = fields.Char('Font Color')
    background_color = fields.Char('Background Color')

    _sql_constraints = [('th_modifier_categ_name_unique', 'unique(name)',
                         'Modifier Category with same name is '
                         'already exists.')]


class ThMenuCategory(models.Model):
    _name = 'th.menu.category'
    _description = 'TH Menu Category'
    _order = 'sequence, name'

    name = fields.Char('Name', index=True, required=True, translate=True)
    parent_id = fields.Many2one('th.menu.category', 'Parent Menu Category',
                                index=True, ondelete='cascade')
    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of menu categories.")

    _sql_constraints = [('th_menu_categ_name_unique', 'unique(name)',
                         'Category with same name is already exists.')]

    @api.multi
    def name_get(self):
        def get_names(cat):
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))
        return True

    @api.multi
    def unlink(self):
        for categ in self:
            if self.search([('parent_id', '=', categ.id)]):
                raise UserError(
                    _('You cannot delete category (%s),\n'
                      'As it is already used as Parent Menu Category.'
                      % categ.display_name))
        return super(ThMenuCategory, self).unlink()
