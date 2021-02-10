from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta
from odoo.addons.resource.models.resource import HOURS_PER_DAY


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    number_of_pb_days = fields.Float('Public Holidays (Days)', readonly=True)
    is_emergency = fields.Boolean('Is Emergency?', default=False,
                                  readonly=True,
                                  states={'draft': [('readonly', False)]})
    outlet_id = fields.Many2one('stock.warehouse', string="Outlet",
                                related='employee_id.outlet_id',
                                states={'draft': [('readonly', False)]})
    attachment_count = fields.Integer('Number of Attachments',
                                      compute='compute_attachment_count')
    attachment_count_stored = fields.Integer('Number of Attachments',
                                             related='attachment_count',
                                             store=True)
    refuse_note = fields.Text('Refuse Note')
    state = fields.Selection(default='draft')

    @api.onchange('date_from', 'date_to')
    def _onchange_public_holiday(self):
        if self.date_from and self.date_to:
            self.number_of_pb_days = self.env[
                'hr.holidays'].get_days_match(self.date_from,
                                              self.date_to)
        else:
            self.number_of_pb_days = 0

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        super(HrLeave, self)._onchange_employee_id()
        employee = self.env['hr.employee'].browse(self.employee_id.id)
        res = {'domain': {'holiday_status_id': [('valid', '=', True)]}}
        # filter based on marital status
        res['domain']['holiday_status_id'] += [
            '|', ('marital_status', '=', employee.marital_status.id),
            ('marital_status', '=', False)]
        employee_types = employee.category_ids
        # filter based on employee type
        res['domain']['holiday_status_id'] += [
            '|', ('employee_type', 'in', employee_types.ids),
            ('employee_type', '=', False)]
        # filter based on employee gender
        res['domain']['holiday_status_id'] += [
            '|', ('gender', '=', employee.gender),
            ('gender', '=', False)]
        return res

    @api.multi
    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        """
        Override this function to deduct the number of hour when request period
        include public holidays
        """
        for holiday in self:
            calendar = holiday.employee_id.resource_calendar_id or self.env.user.company_id.resource_calendar_id
            if holiday.date_from:
                if holiday.date_to:
                    number_of_hours = calendar.get_work_hours_count(
                        holiday.date_from, holiday.date_to)
                    number_of_hours -= holiday.number_of_pb_days * HOURS_PER_DAY
                    holiday.number_of_hours_display = number_of_hours or holiday.number_of_days * HOURS_PER_DAY
            else:
                holiday.number_of_hours_display = 0

    @api.multi
    def check_leave_applicable(self):
        for leave in self:
            h_status = leave.holiday_status_id.id
            holiday_status = self.env['hr.leave.type'].browse(h_status)
            employee_id = leave.employee_id.id
            date_from = leave.request_date_from
            today_date = (datetime.now() + timedelta(hours=8)).date()
            # getting leaves of the employee that have no attachment
            leaves_wo_attachment = self.env['hr.leave'].search([
                ('employee_id', '=', employee_id),
                ('holiday_status_id', '=', h_status),
                ('attachment_count_stored', '=', 0),
                ('state', 'not in', ['draft', 'refuse', 'cancel']),
                ('date_from', '>=', date(today_date.year, 1, 1)),
                ('date_to', '<=', date(today_date.year, 12, 31))
            ])
            # getting apply in advance from leave
            advance_days = holiday_status.apply_advance

            if leave.number_of_days_display <= 0 and leave.number_of_pb_days > 0:
                raise UserError(_('The requested leave period is public '
                                  'holiday(s).Not allow to apply leave.'))
            if holiday_status.attachment_required:
                if holiday_status.max_days_wo_attachment and \
                        holiday_status.max_days_wo_attachment \
                        <= len(leaves_wo_attachment):
                    raise UserError(_(
                        'User have exceeded the maximum number of days - %s '
                        '(applied without attachment) for this Leave Type.'
                        '\nPlease also check leave request(s) in To Approve state.'
                        '\n\nPlease attach attachment instead.')
                                    % holiday_status.max_days_wo_attachment)
            if advance_days > 0:
                days_diff = (datetime.strptime(str(date_from),
                                               '%Y-%m-%d').date() - today_date).days
                if not holiday_status.unpaid:
                    if days_diff < advance_days and not leave.is_emergency:
                        view = self.env.ref(
                            'th_leaves.emergency_confirmation_view')
                        return {
                            'name': _('Apply Emergency Leave?'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'emergency.confirmation',
                            'view_id': False,
                            'target': 'new',
                        }

    @api.multi
    def action_confirm(self):
        for leave in self:
            res = leave.check_leave_applicable()
            if res:
                return res

        return super(HrLeave, self).action_confirm()

    @api.multi
    def action_refuse(self):
        for leave in self:
            if not leave.refuse_note:
                view = self.env.ref('th_leaves.view_refuse_note')
                return {'name': _('Refuse Note'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'refuse.note',
                        'view_id': False,
                        'target': 'new'}

        return super(HrLeave, self).action_refuse()

    @api.multi
    def compute_attachment_count(self):
        Attachment = self.env['ir.attachment']
        for leave in self:
            leave.attachment_count = Attachment.search_count([
                ('res_model', '=', 'hr.leave'), ('res_id', '=', leave.id)])

    @api.multi
    def write(self, vals):
        for leave in self:
            if 'state' in vals or 'refuse_note' in vals or 'manager_id' in vals:
                return super(HrLeave, self).write(vals)
            if leave.state == 'confirm':
                raise UserError(
                    _('User are NOT allow to edit after confirmed.'))

        return super(HrLeave, self).write(vals)
