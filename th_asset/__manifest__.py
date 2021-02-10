{
    'name': 'TH - Assets',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Accounting',
    'description': """
TH - Assets
==============
""",
    'website': 'https://on.net.my/',
    'depends': ['odoo_asset_transfer_ce',
                'report_xlsx_helper',
                'th_product_expiry_date', 'th_account',
                'purchase', 'th_stock'],
    'data': [
        'security/ir.model.access.csv',

        'views/res_config_settings_view.xml',
        'views/account_invoice_view.xml',
        'views/account_asset_view.xml',
        'views/asset_accountability_transfer_view.xml',
        'views/asset_transfer_type_view.xml',
        'views/product.xml',
        'views/production_lot.xml',
        'views/stock_move_line.xml',
        'views/outlet_opening_checklist.xml',

        'wizard/asset_form_capitalised_wizard_view.xml',
        'wizard/fixed_asset_register.xml',
        'wizard/bill_asset_cancellation_wizard.xml',
        'wizard/outlet_opening_checklist_wizard.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
