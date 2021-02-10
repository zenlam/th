{
    'name': 'TH - PoS Lock Screen',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'description': """
TH - PoS Lock Screen
====================
Improved Lock Screen feature which is given by Odoo.

Added auto lock screen feature, if screen is idle for specific time
(which is configure by User).
""",
    'website': 'https://on.net.my/',
    'depends': ['th_outlet'],
    'data': [
        'views/templates.xml',
        'views/pos_config_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
