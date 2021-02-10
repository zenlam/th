{
    'name': 'TH - Purchase Reports',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Purchases',
    'description': """
TH - Purchase Reports
=========================================================
""",
    'website': 'https://on.net.my/',
    'depends': ['purchase', 'report_xlsx_helper'],
    'data': [
        'wizard/purchase_price_history.xml',
        'wizard/po_not_fully_invoiced.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
