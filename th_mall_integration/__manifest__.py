{
    'name': 'TH - Mall Integration',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Tim Hortons',
    'description': """
TH - Mall Integration
=====================
""",
    'website': 'https://on.net.my/',
    'depends': ['point_of_sale', 'web'],
    'data': [
        'security/ir.model.access.csv',

        'views/file_transfer_config.xml',
        'views/file_transfer_log.xml',
        'views/file_transfer_summary.xml',
        'views/request_config.xml',
        'views/request_log.xml',

        'wizard/run_request_config.xml',
        'wizard/pos_order_summary_report.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
