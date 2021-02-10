from odoo import api, fields, models, _
import calendar
import math
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta


class MaritalStatus(models.Model):
    _name = "marital.status"

    name = fields.Char(string="Marital Status", required=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    marital_status = fields.Many2one('marital.status', string="Marital Status")
    outlet_id = fields.Many2one('stock.warehouse', string="Outlet",
                                domain="[('is_outlet', '=', True)]")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ])

    @api.onchange('marital')
    def onchange_marital(self):
        if self.marital:
            status = dict(self._fields['marital'].selection).get(self.marital)
            self.marital_status = self.env['marital.status'].search(
                [('name', '=ilike', status)])
        else:
            self.marital_status = False

    @api.multi
    def get_year_day(self, year):
        if calendar.isleap(year):
            return 366
        return 365

    @api.multi
    def check_overtaken_leave(self):
        for employee in self:
            if not employee.service_termination_date:
                raise UserError(
                    _("Please fill in service termination date before"
                      "checking overtaken leave for employee"))
            legal_leave = self.env['hr.leave.type'].search(
                [('allow_carry', '=', True)])
            if not legal_leave:
                raise UserError(_(
                    "No Legal Leave created or Legal Leave created"
                    " without allow carry forward"))
            leave_result = legal_leave.get_days(employee.id)
            leave_dict = leave_result[legal_leave.id]
            leave_taken = leave_dict['leaves_taken']
            year_day = self.get_year_day(
                employee.service_termination_date.year)
            if employee.service_start_date.year != \
                    employee.service_termination_date.year:
                work_day = (employee.service_termination_date - date(
                    employee.service_termination_date.year, 1, 1)).days + 1
            else:
                work_day = (employee.service_termination_date -
                            employee.service_start_date).days + 1
            period_leave_entitled = (work_day / year_day) * leave_dict[
                'max_leaves']
            frac, whole = math.modf(round(period_leave_entitled, 1))
            if frac >= 0.8:
                period_leave_entitled = round(period_leave_entitled)
            else:
                period_leave_entitled = whole
            if leave_taken > period_leave_entitled:
                leave_overtaken = leave_taken - period_leave_entitled
                msg = 'This employee have %s days(s) of overtaken leave' \
                      % leave_overtaken
            else:
                msg = 'This employee have no record of overtaken leave'

            raise UserError(msg)

    @api.multi
    def allocate_leave(self):
        """
        This function will be use for one time only, for new employee only,
        so, when we create first allocation for new employee, the allocation
        day will be follow day with service year = 1, and then on first day of
        next year, when I want to allocate leave, your service year is still 1
        """
        today = (datetime.now() + timedelta(hours=8)).date()
        for employee in self:
            allocation = self.env['hr.leave.allocation'].search_count(
                [('employee_id', '=', employee.id)])
            if allocation:
                raise UserError(
                    _("This employee already have leave allocated!"))
            if not employee.service_start_date:
                raise UserError(_("Please fill in service start date before"
                                  "allocate leave for employee"))

            year_day = self.get_year_day(
                employee.service_start_date.year)
            service_year = 1
            leave_entitled = self.env['hr.leave.entitled'].search(
                [('position_id', '=', employee.job_id.id),
                 ('service_year', '=', service_year)], limit=1)
            if not leave_entitled:
                raise UserError(
                    _('There is no configuration of number of leave'
                      'for this position with service year of 1 year.\n'
                      'Please configure it in employee position form.'))
            leave_types = self.env['hr.leave.type'].search([
                ('valid', '=', True),
                '|', ('marital_status', '=', employee.marital_status.id),
                ('marital_status', '=', False),
                '|', ('employee_type', 'in', employee.category_ids.ids),
                ('employee_type', '=', False),
                '|', ('gender', '=', employee.gender), ('gender', '=', False),
                ('carry_forward_of', '=', False)])
            for leave in leave_types:
                if leave.allow_carry:
                    period = (date(employee.service_start_date.year, 12,
                                   31) - employee.service_start_date).days + 1
                    number_per_interval = (period / year_day) * \
                                          leave_entitled.day_entitled
                    frac, whole = math.modf(round(number_per_interval, 1))
                    if frac >= 0.8:
                        number_per_interval = round(number_per_interval)
                    else:
                        number_per_interval = whole
                    new_allocation = self.env['hr.leave.allocation'].create({
                        'validity_start': today,
                        'validity_stop': date(today.year, 12, 31),
                        'number_of_days': number_per_interval,
                        'holiday_type': 'employee',
                        'employee_id': employee.id,
                        'unit_per_interval': 'days',
                        'number_per_interval': leave_entitled.day_entitled,
                        'accrual': True,
                        'holiday_status_id': leave.id
                    })
                elif leave.default_day:
                    new_allocation = self.env['hr.leave.allocation'].create({
                        'validity_start': today,
                        'validity_stop': date(today.year, 12, 31),
                        'number_of_days': leave.default_day,
                        'holiday_type': 'employee',
                        'employee_id': employee.id,
                        'unit_per_interval': 'days',
                        'number_per_interval': leave.default_day,
                        'accrual': True,
                        'holiday_status_id': leave.id
                    })
                else:
                    continue
                new_allocation.action_approve()
