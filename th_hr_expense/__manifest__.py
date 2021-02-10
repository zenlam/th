{
    'name': 'TH - Expenses',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Human Resources',
    'description': """
TH - Manage expenses by Employees
=========================================================
""",
    'website': 'https://on.net.my/',
    'depends': ['hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_expense_security.xml',
        'data/mail_data.xml',
        'views/hr_expense.xml',
        'views/hr_expense_category.xml',
        'views/hr_employee.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
