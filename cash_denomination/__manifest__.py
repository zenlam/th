{
    'name': 'Cash Denomination',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'summary': 'Allow Odoo to manage cash denomination',
    'description': "",
    'website': 'https://on.net.my/',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'data/cash_denomination_data.xml',
        'security/cash_denomination_security.xml',
        'security/ir.model.access.csv',
        'views/cash_denomination_view.xml',
        'views/pos_config_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': False,
}
