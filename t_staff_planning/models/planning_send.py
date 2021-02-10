from odoo import fields, models, api
from datetime import datetime


class PlanningSend(models.Model):
    _name = "planning.send"

    start_date = fields.Datetime(string="Start Date", readonly=True)
    end_date = fields.Datetime(string="End Date", readonly=True)
    company_id = fields.Many2one(string="Company", comodel_name="res.company")
    note = fields.Text(string="Additional Message")

    @api.model
    def get_form_view_id(self, access_uid=None):
        return self.env.ref('t_staff_planning.staff_planning_send_form_view').id

    @api.multi
    def get_logo(self):
        return self.company_id.logo.decode("utf-8")

    @api.multi
    def convert_date(self, date):
        return date.strftime("%d/%m/%Y %H:%M %p")

    @api.multi
    def send_schedule(self):
        employee_ids = list(set(self.env.context.get('employee_ids')))
        employee_ids = self.env['hr.employee'].browse(employee_ids)
        ctx = self.env.context
        for employee in employee_ids:
            mail_template_view = self.env.ref('t_staff_planning.planning_send_email_template')
            mail_template_view.with_context({'host': "http://truongdung.com", 'employee': employee,
                                             'label_display': ctx.get('label_display'),
                                             'host': ctx.get('host'),
                                             'host_url': ctx.get('host_url')}).send_mail(self.id, force_send=True)


PlanningSend()
