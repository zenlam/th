{
    'name': 'TH - Promotion',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'description': """
TH - Promotion
==============
""",
    'website': 'https://on.net.my/',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/promotion_category.xml',
        'views/promotion.xml',
        'views/templates.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
