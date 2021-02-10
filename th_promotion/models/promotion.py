from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ThPromotion(models.Model):
    _name = 'th.promotion'
    _description = 'TH Promotion'

    name = fields.Char(string="Name", required=True)
    internal_name = fields.Char(string="Internal Name", required=True)
    code = fields.Char(string="Code", required=True)
    category_id = fields.Many2one('th.promotion.category', string="Category",
                                  required=True)
    apply_for = fields.Selection(string="Apply Object",
                                 selection=[('product', 'Product'),
                                            ('bill', 'Whole Bill')],
                                 default='product', required=True)
    is_over_promotion = fields.Boolean(string="Apply Over Promotions",
                                    default=False)
    image = fields.Binary("Image", attachment=True)
    is_voucher = fields.Boolean(string="Voucher", default=False)
    is_manager_approve = fields.Boolean(string="Manager Approval", default=False)
    active = fields.Boolean(string="Active", default=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date")
    membership_ids = fields.Char(string="Membership Groups")
    is_member_birthday = fields.Boolean(string="Member Birthday", default=False)
    outlet_ids = fields.Many2many('stock.warehouse', string="Outlet")
    birthday_period = fields.Integer(string="Birthday Period (month)")
    # 'Promotion Rules' tab
    promotion_rule_ids = fields.One2many('th.promotion.rule', 'promotion_id',
                                         string="Promotion Rules")
    # 'Time' tab
    recurring = fields.Selection(
        selection=[('week', 'By Week'), ('month', 'By Month'), 
                   ('year', 'By Year')],
        string="Recurring"
    )
    monday = fields.Boolean(default=False, string="Monday")
    tuesday = fields.Boolean(default=False, string="Tuesday")
    wednesday = fields.Boolean(default=False, string="Wednesday")
    thursday = fields.Boolean(default=False, string="Thursday")
    friday = fields.Boolean(default=False, string="Friday")
    saturday = fields.Boolean(default=False, string="Saturday")
    sunday = fields.Boolean(default=False, string="Sunday")

    promotion_time_week_ids = fields.One2many(
        comodel_name='th.promotion.time',
        inverse_name='promotion_week_id',
        string='Promotion Time Week'
    )
    promotion_time_month_ids = fields.One2many(
        comodel_name='th.promotion.time',
        inverse_name='promotion_month_id',
        string='Promotion Time Month'
    )
    promotion_time_year_ids = fields.One2many(
        comodel_name='th.promotion.time',
        inverse_name='promotion_year_id',
        string='Promotion Time Year'
    )

    @api.onchange('apply_for')
    def onchange_apply_for(self):
        self.promotion_rule_ids = False

    @api.constrains('name')
    def check_name_unique(self):
        promotions = self.env['th.promotion'].search([('id', '!=', self.id)])
        for promotion in promotions:
            if self.name and self.name.replace(" ", "").lower() == \
                    promotion.name.replace(" ", "").lower():
                raise ValidationError(_("Promotion name already exists!"))

    @api.constrains('code')
    def check_code_unique(self):
        promotions = self.env['th.promotion'].search([('id', '!=', self.id)])
        for promotion in promotions:
            if self.code and self.code.replace(" ", "").lower() == \
                    promotion.code.replace(" ", "").lower():
                raise ValidationError(_("Promotion code already exists!"))
