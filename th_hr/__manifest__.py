{
    'name': 'TH HR',
    'summary': 'TH HR',
    'version': '1.0',
    'category': 'Hr',
    'description': """
        TH HR
    """,
    'depends': ['hr'],
    'data': [
        'views/hr_job_view.xml',
        'views/hr_employee_view.xml',
        'views/working_time_rules_view.xml',
        'security/ir.model.access.csv',
    ],
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
