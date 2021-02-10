from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ThPromotionCategory(models.Model):
    _name = 'th.promotion.category'
    _description = 'TH Promotion Category'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    parent_category = fields.Many2one('th.promotion.category', string="Parent")
    active = fields.Boolean(string="Active", default=True)

    @api.constrains('code')
    def check_code_unique(self):
        categories = self.env['th.promotion.category'].search([
            ('id', '!=', self.id)
        ])
        for category in categories:
            if self.code and self.code.replace(" ", "").lower() == \
                    category.code.replace(" ", "").lower():
                raise ValidationError(_("Category code already exists!"))

    @api.constrains('name')
    def check_name_unique(self):
        categories = self.env['th.promotion.category'].search([
            ('id', '!=', self.id)
        ])
        for category in categories:
            if self.name and self.name.replace(" ", "").lower() == \
                    category.name.replace(" ", "").lower():
                raise ValidationError(_("Category name already exists!"))
