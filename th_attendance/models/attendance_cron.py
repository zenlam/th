from odoo import fields, models, api, tools, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
import os
from os import path
from datetime import datetime
import base64


class AttendanceCron(models.Model):
    _name = "attendance.cron"
    _inherits = {'ir.cron': 'cron_id'}
    _description = "Attendances Upload Automation"

    @api.model
    def default_name(self):
        return str(fields.Date.today()) + '_attendance.csv'

    # name = fields.Char(default=_("Auto Upload Attendance List"), readonly=True)
    file_msg = fields.Char(readonly=1, compute="_compute_msg")
    file_msg_err = fields.Char(readonly=1, compute="_compute_msg")
    cron_id = fields.Many2one('ir.cron', 'Schedule Action', ondelete="cascade", required=True, auto_join=True)
    file_path = fields.Char('File Path', required=True)
    file_name = fields.Char('File Name', required=True)
    schedule_time = fields.Datetime('Schedule Time')

    @api.depends('file_path', 'file_name')
    def _compute_msg(self):
        if self.file_path and self.file_name:
            file_path = self.get_file_path(self.file_path, self.file_name)
            if path.exists(file_path):
                self.file_msg = "File path is correct."
                self.file_msg_err = False
            else:
                self.file_msg_err = "File path is not correct."
                self.file_msg = False

    @api.model
    def get_file_path(self, file_path, file_name):
        today_date = datetime.today().strftime('%Y%m%d')
        return '%s/%s_%s.CSV' % (file_path, file_name, today_date)

    @api.multi
    def test(self):
        self.env['hr.attendance'].do()


AttendanceCron()
