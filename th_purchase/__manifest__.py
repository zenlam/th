{
    'name': 'TH - Purchase',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Purchases',
    'description': """
TH - Purchase Orders
=========================================================
""",
    'website': 'https://on.net.my/',
    'depends': ['purchase'],
    'data': [
        'security/security.xml',
        'views/res_config_settings_views.xml',
        'views/purchase_view.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
