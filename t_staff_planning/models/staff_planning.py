from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class StaffPlanning(models.Model):
    _name = "staff.planning"

    employee_id = fields.Many2one(string="Employee", comodel_name="hr.employee")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    role_id = fields.Many2one(string="Role", comodel_name="planning.role")
    company_id = fields.Many2one(string="Company", comodel_name="res.company")
    user_id = fields.Many2one(string="User", comodel_name="res.users", related="employee_id.user_id")
    outlet_id = fields.Many2many(comodel_name='stock.warehouse', string="Outlet")
    allocated_hours = fields.Float(string="Allocated Hours", compute="_compute_allocated_hours", store=True)
    sd_working_time = fields.Float(string="Working Time Hours", related="employee_id.job_id.working_time_rule_id.sd_working_t")
    colour = fields.Char(string="Colour", related='role_id.colour')
    checked = fields.Boolean(String="Check", help="Check")
    image_small = fields.Binary(string="Small-sized photo", attachment=True,related="employee_id.image_small")

    # @api.depends('allocated_hours', 'employee_id')
    # def _compute_check_allocated_hours(self):
    #     sd_working_time = self.employee_id.job_id.working_time_rule_id.sd_working_t
    #     if sd_working_time and self.allocated_hours > sd_working_time:
    #         pass

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.company_id = self.employee_id.user_id.company_id
        if not self.role_id:
            self.role_id = self.employee_id.role_id.id

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        self.allocated_hours = self.get_diff_hours(self.start_date, self.end_date, self.employee_id)
        working_time_rule = self.employee_id.job_id.working_time_rule_id
        s_working_time = working_time_rule.sd_working_t + working_time_rule.max_ot
        if self.start_date and self.end_date:
            public_holiday = self.env['hr.holidays'].get_days_match(self.start_date, self.end_date, self.employee_id.id)
            if public_holiday > 0:
                s_working_time = working_time_rule.ph_working_time + working_time_rule.max_ot
        if self.allocated_hours > s_working_time:
            raise ValidationError(" Planned working time do not exceed the value configured in Standard Working Time !")

    @api.depends('start_date', 'end_date')
    def _compute_allocated_hours(self):
        for plan in self:
            plan.allocated_hours = self.get_diff_hours(plan.start_date, plan.end_date, plan.employee_id)

    @api.model
    def get_diff_hours(self, start_date, end_date, employee_id):
        if start_date and end_date:
            if type(start_date) is str:
                start_date = datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT)
                end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATETIME_FORMAT)
            diff = (end_date - start_date)
            days = diff.days
            seconds = diff.seconds
            res = (days * 24 * 60 * 60 + seconds) / 3600
            working_time_rule = employee_id.job_id.working_time_rule_id
            if working_time_rule and res > 0:
                res -= working_time_rule.sd_break_time
            return res
        return 0

    @api.model
    def get_form_view_id(self, access_uid=None):
        return self.env.ref('t_staff_planning.staff_planning_form_view').id

    @api.model
    def get_data(self, domain, domain_hr=[]):
        # staff_data = list(filter(lambda l: l['start_date'] <= l['end_date'], staff_data))
        # my shift
        outlet_ids = self.env.user.user_outlet_ids.ids + self.env.user.manager_outlet_ids.ids
        new_domain = []
        for x in domain:
            if 'outlet_id' in x and x[2]:
                outlet_ids = [x[2]]
            if 'outlet_id' not in x:
                new_domain.append(x)
        staff_data = self.search(new_domain)
        staff_id = []
        employee_show = []

        for x in staff_data:
            user_id = x.employee_id.user_id
            if user_id and outlet_ids:
                ol_ids = [i.id for i in user_id.user_outlet_ids if i.id in outlet_ids]
                mg_outlet_ids = [i.id for i in user_id.manager_outlet_ids if i.id in outlet_ids]
                if len(ol_ids) > 0 or len(mg_outlet_ids) > 0:
                    employee_show.append(x.employee_id.id)
                    staff_id.append(x)
        staff_id = [x.id for x in staff_id]
        staff_data = self.search_read([['id', 'in', staff_id]])
        cost = self.cal_cost(self.search([['id', 'in', staff_id]]))
        domain_hr.append(['id', 'in', employee_show])
        employee_data = self.env['hr.employee'].search(domain_hr)
        _employee_data = []
        for employee in employee_data:
            _employee_data.append({'id': employee.id, 'name': employee.name, 'role_id': employee.role_id.id, 'role_name': employee.role_id.name,
                                   'color': employee.role_id.colour, 'image_small': employee.image_small})
        return {'staff_data': staff_data, 'employee_data': _employee_data,
                'outlet_manager_ids': self.env.user.manager_outlet_ids.ids, 'cost': cost,
                'isManager': len(self.env.user.manager_outlet_ids.ids) > 0 or self.env.ref('point_of_sale.group_pos_manager') in self.env.user.groups_id}

    @api.model
    def copy_previous_week(self, data):
        rs = False
        for d in data:
            rs = self.create(d)
        return rs

    @api.model
    def cal_cost(self, data):
        result = {'labor_cost': 0, 'working_hours': 0, 'ot_hours': 0}

        def format_wt(d):
            return ('{:%s,.2f}' % len(str(d))).format(d)

        for x in data:
            if x.start_date and x.end_date:
                days_matched = self.env['hr.holidays'].with_context(force=True).get_days_match(x.start_date, x.end_date)
                job = x.employee_id.job_id
                allocated_hours = x.allocated_hours*60
                labor_cost = job.default_labour_cost
                working_time_rule = job.working_time_rule_id
                working_time = working_time_rule.ph_working_time*60 if days_matched > 0 \
                    else working_time_rule.sd_working_t*60
                # sd_break_time = convert(working_time_rule.sd_break_time)
                ot_break_time = working_time_rule.ot_break_time*60
                max_ot = working_time_rule.max_ot*60
                # ph_working_time = convert(working_time_rule.ph_working_time)
                ot_time = 0
                if allocated_hours > working_time:
                    wkt = working_time
                    ot_time = allocated_hours - working_time - ot_break_time
                    ot_time = ot_time if ot_time <= max_ot else max_ot
                else:
                    wkt = allocated_hours
                cost = (wkt+ot_time) / 60 * labor_cost
                if days_matched > 0:
                    wkt = wkt*2
                    ot_time = ot_time*2
                    cost = cost*2
                result['working_hours'] += wkt
                result['ot_hours'] += ot_time
                result['labor_cost'] += cost
        result['working_hours'] = format_wt(result['working_hours']/60)
        result['ot_hours'] = format_wt(result['ot_hours']/60)
        result['labor_cost'] = format_wt(result['labor_cost'])
        return result


StaffPlanning()
