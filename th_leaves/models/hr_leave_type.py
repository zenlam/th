from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta
from odoo.tools.float_utils import float_round


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    attachment_required = fields.Boolean('Requires Attachment', default=False)
    max_days_wo_attachment = fields.Integer("Max Days without Attachment")
    employee_type = fields.Many2many('hr.employee.category',
                                     'leave_employee_category_rel',
                                     string="Employee Type")
    marital_status = fields.Many2many('marital.status',
                                      'leave_marital_status_rel',
                                      string='Marital Status')
    apply_advance = fields.Integer('Apply in Advance of', required=True)
    allow_carry = fields.Boolean('Allow Carry Forward', default=False)
    carry_forward_of = fields.Many2one('hr.leave.type',
                                       string='Carry Forward Of')
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female')], string="Gender")
    default_day = fields.Integer('Default Day(s)',
                                 help="Default Day of Leave for each employee."
                                      "Put 0 for leave type which the leave "
                                      "day is not fixed, like Annual Leave")


    @api.constrains('allow_carry')
    def check_allow_carry(self):
        if self.allow_carry:
            leave_with_carry = self.env['hr.leave.type'].search_count(
                [('allow_carry', '=', True)])
            if leave_with_carry > 1:
                raise UserError(_("Only ONE Leave Type can be carry forward!"))

    @api.constrains('apply_advance')
    def check_apply_advance(self):
        if self.apply_advance < 0:
            raise UserError(_("Apply in Advance of Day(s) can't be Negative."))

    @api.constrains('attachment_required', 'max_days_wo_attachment')
    def check_max_days_wo_attachment(self):
        if self.attachment_required and self.max_days_wo_attachment < 0:
            raise UserError(
                _("Max Days without Attachment can't be Negative."))

    @api.model
    def create(self, vals):
        res = super(HrLeaveType, self).create(vals)
        if vals.get('allow_carry', False):
            res.copy({
                'name': ('Carry Forward of ' + res['name']),
                'start_date': (datetime.now() + timedelta(hours=8)).date(),
                'allow_carry': False,
                'carry_forward_of': res.id
            })
        return res

    @api.multi
    def get_days(self, employee_id):
        """
        Overwrite this function to get request and allocation for current year
        """
        # need to use `dict` constructor to create a dict per id
        today = (datetime.now() + timedelta(hours=8)).date()
        result = dict((id,
                       dict(max_leaves=0, leaves_taken=0, remaining_leaves=0,
                            virtual_remaining_leaves=0)) for id in self.ids)

        requests = self.env['hr.leave'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids),
            ('date_from', '>=', date(today.year, 1, 1)),
            ('date_to', '<=', date(today.year, 12, 31))
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids),
            ('validity_start', '<=', today),
            ('validity_stop', '>=', today)
        ])

        for request in requests:
            status_dict = result[request.holiday_status_id.id]
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
            status_dict = result[allocation.holiday_status_id.id]
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
        return result

    @api.multi
    def name_get(self):
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HrLeaveType, self).name_get()
        res = []
        for record in self:
            name = record.name
            if record.virtual_remaining_leaves < 0:
                record.virtual_remaining_leaves = 0
            if record.allocation_type != 'no':
                name = "%(name)s (%(count)s)" % {
                    'name': name,
                    'count': _('%g remaining out of %g') % (
                        float_round(record.virtual_remaining_leaves,
                                    precision_digits=2) or 0.0,
                        float_round(record.max_leaves,
                                    precision_digits=2) or 0.0,
                    ) + (_(' hours') if record.request_unit == 'hour' else _(
                        ' days'))
                }
            res.append((record.id, name))
        return res
