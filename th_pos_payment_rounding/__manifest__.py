{
    'name': 'TH - POS Payment Rounding',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'description': """
TH - Point of Sale Payment Rounding
======================================
""",
    'website': 'https://on.net.my/',
    'depends': ['th_point_of_sale'],
    'data': [
        'views/account_statement_view.xml',
        'views/templates.xml'
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
