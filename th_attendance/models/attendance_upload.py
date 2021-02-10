# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrAttendanceUpload(models.TransientModel):
    _name = 'hr.attendance.upload'

    attachment_ids = fields.Many2many('ir.attachment', string='Files')

    def import_data(self):
        self.env['hr.attendance'].do(self.attachment_ids)


HrAttendanceUpload()
