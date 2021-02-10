from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ThPromotionRule(models.Model):
    _name = 'th.promotion.rule'
    _description = 'TH Promotion Rule'

    promotion_id = fields.Many2one('th.promotion', string="Promotion")
    name = fields.Char(string="Name", required=True)
    is_bundle = fields.Boolean(string="Bundle Item", default=False)
    apply_menu_ids = fields.Many2many('product.product',
                                      'promotion_rule_menu_rel',
                                      string="Applied Menu Names")
    apply_category_ids = fields.Many2many('pos.category',
                                          'promotion_rule_categ_rel',
                                          string="Applied Categories")
    exclude_menu_ids = fields.Many2many('product.product',
                                        'promotion_rule_exclude_menu_rel',
                                        string="Except Menu Names")
    exclude_category_ids = fields.Many2many('pos.category',
                                            'promotion_rule_exclude_categ_rel',
                                            string="Except Categories")
    condition = fields.Selection(
        selection=[('amount', 'Min Amount'), ('quantity', 'Min Quantity')],
        string="Condition")
    condition_value = fields.Integer(string="Condition Value")
    is_product_group = fields.Boolean(string="Product Group", default=False)
    discount_type = fields.Selection(
        selection=[('percentage', 'Percentage'), ('amount', 'Amount')],
        string="Discount Type", default='percentage')
    discount_value = fields.Float(string="Disc. Value")
    max_discount_value = fields.Float(string="Max Disc. Value")

    @api.onchange('condition')
    def check_onchange_condition(self):
        if self.condition == 'amount' and \
                self.promotion_id.apply_for == 'product':
            raise ValidationError(
                _('Product Promotion only support condition is quantity!'))
        if self.condition == 'quantity' and \
                self.promotion_id.apply_for == 'bill':
            raise ValidationError(
                _('Whole Bill Promotion only support condition is amount!'))
