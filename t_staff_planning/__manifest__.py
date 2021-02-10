{
    'name': 'Staff Planning',
    'summary': 'Staff Planning',
    'version': '1.0',
    'category': 'Staff',
    'description': """
        Staff Planning
    """,
    'depends': ['web', 'hr', 'th_hr_holidays', 'point_of_sale', 'th_hr'],
    'data': [
        'views/templates.xml',
        'views/employee_view.xml',
        'views/planning_views.xml',
        'views/planning_email_template.xml',
        'views/planning_send_view.xml',
        'security/staff_planning.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/base.xml',
    ],
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
}
