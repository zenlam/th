{
    'name': 'TH Leaves',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Hidden',
    'description': """
Tim Hortons Leaves
==================
    """,
    'website': 'https://on.net.my/',
    'depends': ['hr', 'hr_employee_service'],
    'data': [
        'views/hr_employee.xml',
        'views/hr_leave.xml',
        'views/hr_leave_allocation.xml',
        'views/hr_leave_type.xml',
        'views/hr_leave_entitled.xml',
        'views/hr_leave_history.xml',
        'views/hr_job.xml',
        'views/res_company.xml',
        'security/ir.model.access.csv',
        'wizard/emergency_confirmation.xml',
        'wizard/refuse_note.xml',
        'data/data.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
