# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID

class PurchaseRequisitionTemplate(models.Model):
    _name = "purchase.requisition.template"

    name = fields.Char('Template Name', required=True)
    code = fields.Char('Code', required=True)
    date_type = fields.Selection([('specific_date','Specific Date'),('pr_create_date','PR Creation Date')],string='Date Based on', required=True)
    start_date = fields.Date("Start From")
    end_date = fields.Date("Start Till")
    last_period = fields.Selection([('day','day(s)'),('weeks','Weeks'),('month','Months')], string='Last')
    last_number = fields.Integer('Last Number')
    monday = fields.Boolean('Monday')
    tuesday = fields.Boolean('Tuesday')
    wednesday = fields.Boolean('Wednesday')
    thursday = fields.Boolean('Thursday')
    friday = fields.Boolean('Friday')
    saturday = fields.Boolean('Saturday')
    sunday = fields.Boolean('Sunday')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', "Requisition Code Already Exist !"),
    ]


