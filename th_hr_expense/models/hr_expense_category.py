from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ThExpenseCategory(models.Model):
    _name = 'th.expense.category'
    _description = 'TH Expense Category'

    name = fields.Char(string="Expense Category", required=True)
    active = fields.Boolean(string="Active", default=True)
    parent_category = fields.Many2one('th.expense.category',
                                      string="Parent Category")
    is_double_validation = fields.Boolean(string="Apply Double Validation",
                                          default=False)
    is_require_attachment = fields.Boolean(string="Require Attachment",
                                           default=False)
    claim_valid_days = fields.Integer(string="Claim Valid Days", required=True)
    amount = fields.Float(string="Amount")

    @api.constrains('name')
    def check_name_unique(self):
        categories = self.env['th.expense.category'].search([
            ('id', '!=', self.id)
        ])
        for category in categories:
            if self.name and self.name.replace(" ", "").lower() == \
                    category.name.replace(" ", "").lower():
                raise ValidationError(_('Category name already exists!'))
