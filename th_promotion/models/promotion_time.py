from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ThPromotionTime(models.Model):
    _name = 'th.promotion.time'
    _description = 'TH Promotion Time'

    promotion_week_id = fields.Many2one(comodel_name='th.promotion',
                                        string="Promotion by Week")
    promotion_month_id = fields.Many2one(comodel_name='th.promotion',
                                         string="Promotion by Month")
    promotion_year_id = fields.Many2one(comodel_name='th.promotion',
                                        string="Promotion by Year")

    date = fields.Date(string="Date", copy=False)
    day_of_month = fields.Integer(string="Day of Month")
    start_hour = fields.Float(string="Start hour")
    end_hour = fields.Float(string="End hour")

    @api.constrains('start_hour', 'end_hour')
    def check_time(self):
        if self.start_hour >= 24 or self.end_hour >= 24:
            raise ValidationError('Time ranging from 00:00 to 23:59 !')
        if self.start_hour < 0 or self.end_hour < 0:
            raise ValidationError('Time ranging from 00:00 to 23:59 !')
        if self.end_hour < self.start_hour:
            raise ValidationError('Start hour must less than End hour')
