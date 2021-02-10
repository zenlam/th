from odoo import fields, models, api, tools, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class AttendanceCron(models.Model):
    _name = "attendance.working.time"

    working_date = fields.Date(string="Date", required=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=True)
    working_hours = fields.Float(string="Working Hours", compute="_compute_working_time", store=True)
    working_time = fields.Float(string="Working Time", compute="_compute_working_time", store=True)
    ot_time = fields.Float(string="OT", compute="_compute_working_time", store=True)
    attendance_ids = fields.One2many('hr.attendance', 'attendance_wt_id', string='Attendances')

    @api.depends('employee_id', 'attendance_ids.check_in', 'attendance_ids.check_out')
    def _compute_working_time(self):
        if self.employee_id and self.attendance_ids:
            working_hours = 0
            for attendance in self.attendance_ids:
                working_hours += (attendance.check_out - attendance.check_in).seconds/60/60
            working_time_rule = self.employee_id.working_time_rule_id
            sd_working_time = working_time_rule.sd_working_t * 60
            sd_break_time = working_time_rule.sd_break_time * 60
            working_hours = working_hours * 60
            working_time = working_hours - sd_break_time
            self.working_hours = working_hours/60
            if working_time > sd_working_time:
                self.working_time = sd_working_time/60
                self.ot_time = (working_time - sd_working_time)/60
            else:
                self.working_time = working_time/60

    @api.model
    def prepare_values_attendance(self, attendance):
        working_hours = 0
        if attendance.check_in and attendance.check_out:
            working_hours = (attendance.check_out - attendance.check_in).seconds/60/60
        return {'employee_id': attendance.employee_id.id,
                'working_date': attendance.check_in.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'working_hours': working_hours}

    @api.model
    def create_working_time(self, attendance):
        date_check = attendance.check_in or attendance.check_out
        if date_check:
            date_check = date_check.strftime(DEFAULT_SERVER_DATE_FORMAT)
            attendance_wt = self.search([['working_date', '=', date_check], ['employee_id', '=', attendance.employee_id.id]])
            if not attendance_wt:
                attendance_wt = self.create(self.prepare_values_attendance(attendance))
            attendance.write({'attendance_wt_id': attendance_wt.id})
        return True


AttendanceCron()
