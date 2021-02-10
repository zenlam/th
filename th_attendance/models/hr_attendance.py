import os
import base64
from odoo import api, fields, models, _


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    attendance_wt_id = fields.Many2one(string="Attendance Working Time", comodel_name="attendance.working.time")

    @api.model
    def prepare_values_schedule(self, values):
        if self.env.context.get('schedule', False):
            employee_id = self.employee_id.search([['xid_mapping', '=', values['employee_id']]])
            values['employee_id'] = employee_id.id
        return values

    @api.model
    def create(self, values):
        values = self.prepare_values_schedule(values)
        res = super(HrAttendance, self).create(values)
        self.env['attendance.working.time'].create_working_time(res)
        return res

    @api.model
    def prepare_import_data(self, attachment=False):
        if attachment:
            values = {'file': base64.b64decode(attachment.datas), 'file_name': attachment.name,
                      'file_type': attachment.mimetype, 'res_model': 'hr.attendance'}
            columns = attachment.index_content.split('\n')[0].split(",")
        else:
            cron_data = self.env.ref('th_attendance.ir_cron_hr_attendance_upload')
            file_path = cron_data.get_file_path(cron_data.file_path, cron_data.file_name)
            _file = open(file_path, 'rb')
            values = {'file': _file.read(), 'file_name': os.path.basename(_file.name), 'file_type': 'text/csv',
                      'res_model': 'hr.attendance'}
            _file.close()
            _file = open(file_path, 'rb')
            header = _file.readline().decode("utf-8").replace("\n", "")
            columns = header.split(",")
            _file.close()
        return {'values': values, 'columns': columns}

    @api.model
    def do(self, attachment=False):
        base_import_mapping = self.env['base_import.mapping']
        import_data = self.prepare_import_data(attachment)
        values = import_data['values']
        columns = import_data['columns']
        _fields = []

        for idx, column_name in enumerate(columns):
            exist_records = base_import_mapping.search([('res_model', '=', 'hr.attendance'),
                                                        ('column_name', '=', column_name)])
            if exist_records:
                _fields.append(exist_records.field_name)
            else:
                _fields.append(column_name)

        base_import = self.env['base_import.import'].create(values)
        field_get = self.fields_get()
        for k, v in enumerate(_fields):
            _field = field_get.get(v, False)
            if _field and _field['type'] == 'many2one':
                _fields[k] = '%s/.%s' % (v, 'id')
        base_import.with_context(schedule=True).import_data(
            _fields, {'headers': True, 'encoding': 'ascii', 'separator': ',',
                      'float_thousand_separator': ',', 'float_decimal_separator': '.',
                      'datetime_format': '%Y/%m/%d %H:%M:%S', 'quoting': '"'})


HrAttendance()
