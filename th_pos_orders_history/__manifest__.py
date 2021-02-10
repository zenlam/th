{
    'name': 'TH - PoS Orders History',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'description': """
TH - PoS Orders History
=======================
""",
    'website': 'https://on.net.my/',
    'depends': ['th_point_of_sale', 'pos_orders_history'],
    'data': [
        'views/templates.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
