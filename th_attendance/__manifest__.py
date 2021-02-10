{
    'name': 'TH HR Attendance',
    'summary': 'TH HR Attendance',
    'version': '1.0',
    'category': 'Hr',
    'description': """
        TH HR Attendance
    """,
    'depends': ['hr_attendance', 'base_import'],
    'data': [
        'views/attendance_cron_view.xml',
        'views/attendance_working_time_view.xml',
        'views/employee_view.xml',
        'views/templates.xml',
        'views/data_cron_attendance.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/attendance_upload_views.xml',
    ],
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
