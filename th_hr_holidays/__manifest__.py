{
    'name': 'TH - HR Holidays',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'HR Holidays',
    'description': """
TH - HR Holidays
==================
""",
    'website': 'https://on.net.my/',
    'depends': ['hr_holidays', 'th_outlet'],
    'data': [
        'views/hr_holidays_view.xml',
        'views/employee_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}