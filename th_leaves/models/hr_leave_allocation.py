from odoo import api, fields, models, _
from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    validity_start = fields.Date(string='Valid From', readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'confirm': [('readonly', False)]},
                                 required=True)
    validity_stop = fields.Date(string='Valid To', readonly=True,
                                states={'draft': [('readonly', False)],
                                        'confirm': [('readonly', False)]},
                                required=True)

    @api.constrains('unit_per_interval')
    def check_unit_per_interval(self):
        for allocation in self:
            if self.accrual == True:
                if allocation.holiday_status_id.request_unit == 'day' \
                        and allocation.unit_per_interval != 'days':
                    raise UserError(_(
                        "The leave type unit is in day, "
                        "but the accrual unit is in hour"))
                if allocation.holiday_status_id.request_unit == 'hour' \
                        and allocation.unit_per_interval != 'hours':
                    raise UserError(_(
                        "The leave type unit is in hour, "
                        "but the accrual unit is in day"))

    @api.multi
    def get_days(self):
        """
        This function mimic how leave type model calculate leave status,
        just with extra domain when filtering requests and allocations.
        The reason of using this function is the number of leave will be reset
        to zero during first day of new year, so we can't directly get the
        remaining leave from the leave type.
        """

        requests = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', '=', self.holiday_status_id.id),
            ('date_from', '>=', date(self.validity_start.year, 1, 1)),
            ('date_to', '<=', date(self.validity_start.year, 12, 31))
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', '=', self.holiday_status_id.id),
            ('validity_start', '>=', date(self.validity_start.year, 1, 1)),
            ('validity_stop', '<=', date(self.validity_start.year, 12, 31))
        ])

        status_dict = dict(max_leaves=0, leaves_taken=0, remaining_leaves=0,
                           virtual_remaining_leaves=0)

        for request in requests:
            status_dict['virtual_remaining_leaves'] -= (
                request.number_of_hours_display
                if request.leave_type_request_unit == 'hour'
                else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)
                status_dict['remaining_leaves'] -= (
                    request.number_of_hours_display
                    if request.leave_type_request_unit == 'hour'
                    else request.number_of_days)

        for allocation in allocations.sudo():
            if allocation.state == 'validate':
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict['virtual_remaining_leaves'] += (
                    allocation.number_of_hours_display
                    if allocation.type_request_unit == 'hour'
                    else allocation.number_of_days)
                status_dict['max_leaves'] += (
                    allocation.number_of_hours_display
                    if allocation.type_request_unit == 'hour'
                    else allocation.number_of_days)
                status_dict['remaining_leaves'] += (
                    allocation.number_of_hours_display
                    if allocation.type_request_unit == 'hour'
                    else allocation.number_of_days)

        return status_dict

    @api.model
    def _update_accrual(self):
        """
            Method called by the cron task in order to increment the number_of_days when
            necessary.
        """
        today = (datetime.now() + timedelta(hours=8)).date()

        holidays = self.search(
            [('accrual', '=', True), ('employee_id.active', '=', True),
             ('state', '=', 'validate'), ('holiday_type', '=', 'employee'),
             ('nextcall', '=', False),
             ('employee_id.service_termination_date', '=', False)])

        for holiday in holidays:
            values = {}

            delta = relativedelta(years=1)

            values['nextcall'] = (holiday.nextcall if holiday.nextcall
                                  else today) + delta

            holiday.write(values)
            # in next year, what is the service year
            service_year = holiday.employee_id.service_duration_years + 1
            leave_entitled = self.env['hr.leave.entitled'].search(
                [('position_id', '=', holiday.employee_id.job_id.id),
                 ('service_year', '=', service_year)], limit=1)
            if holiday.holiday_status_id.allow_carry:
                number_per_interval = leave_entitled.day_entitled if \
                    leave_entitled else holiday.number_per_interval
            else:
                number_per_interval = holiday.number_per_interval
            new_allocation = holiday.create({
                'validity_start': today,
                'validity_stop': date(today.year, 12, 31),
                'number_of_days': holiday.number_per_interval,
                'holiday_type': 'employee',
                'employee_id': holiday.employee_id.id,
                'unit_per_interval': holiday.unit_per_interval,
                'number_per_interval': number_per_interval,
                'accrual': True,
                'holiday_status_id': holiday.holiday_status_id.id
            })
            new_allocation.action_approve()
            # update company carry forward expiry date,
            # only upgrade year for info purpose
            expired_date = holiday.employee_id.company_id.carry_expired_date
            cap_days = holiday.employee_id.company_id.cap_days
            remaining_leaves = holiday.get_days().get('remaining_leaves', 0)
            if expired_date:
                expired_date = date(year=today.year, month=expired_date.month,
                                    day=expired_date.day)
            # only create carry forward allocation for allocation that
            # the leave type is carry forward and have remaining leave
            if holiday.holiday_status_id.allow_carry and remaining_leaves > 0:
                carry_holiday_type = self.env['hr.leave.type'].search(
                    [('carry_forward_of', '=', holiday.holiday_status_id.id)])

                carry_allocation = holiday.create({
                    'validity_start': today,
                    'validity_stop': expired_date,
                    'number_of_days': min(remaining_leaves,
                                          cap_days) if cap_days > 0 else remaining_leaves,
                    'holiday_type': 'employee',
                    'employee_id': holiday.employee_id.id,
                    'unit_per_interval': holiday.unit_per_interval,
                    'accrual': False,
                    'holiday_status_id': carry_holiday_type.id
                })
                carry_allocation.action_approve()
