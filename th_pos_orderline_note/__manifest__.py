{
    'name': 'TH - PoS Orderline Note',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'description': """
TH - PoS Orderline Note
=======================
This feature is already taken from ``pos_restaurant`` module of Odoo S.A.

With extended functionality of "Quick Notes"

It allows to create notes & select notes in Orderline instead of writing it.
""",
    'website': 'https://on.net.my/',
    'depends': ['th_point_of_sale'],
    'data': [
        'security/ir.model.access.csv',

        'views/templates.xml',
        'views/pos_orderline_note_views.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
