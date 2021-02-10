{
    'name': 'TH - PoS Receipt',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'description': """
TH - PoS Receipt
====================
""",
    'website': 'https://on.net.my/',
    'depends': ['th_pos_payment_rounding'],
    'data': [
        'views/res_company_view.xml'
    ],
    'qweb': ['static/src/xml/pos_receipt.xml'],
    'installable': True,
    'auto_install': False,
}
