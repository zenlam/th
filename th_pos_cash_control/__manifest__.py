{
    'name': 'Tim Hortons - POS Cash Control',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'summary': 'Manage the POS cash control of Tim Horton',
    'description': "",
    'website': 'https://on.net.my/',
    'depends': [
        'cash_denomination',
        'th_point_of_sale',
    ],
    'data': [
        'security/cash_control_security.xml',
        'security/ir.model.access.csv',
        'views/account_journal_view.xml',
        'views/cash_control_view.xml',
        'views/cash_in_out_log_view.xml',
        'views/pos_config_view.xml',
        'views/pos_session_view.xml',
        'views/store_management_view.xml',
        'wizard/pos_box_view.xml',
        'wizard/pos_session_closing_confirm_view.xml'
    ],
    'qweb': [],
    'installable': True,
    'application': False,
}
