# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.

{
    'name':'Asset Dashboard',
    'category': 'Accounting',
    'price': 49.0,
        'version':'1.1',

    'currency': 'EUR',
    'summary': 'Asset Dashboard.',
    'license': 'Other proprietary',
    'description': """
Asset Dashboard
This module add Asset dashboard view for Asset
Asset Dashboard
Dashboard for Asset
account asset
asset
dashboard asset
asset close
asset dispose
asset disposal
account asset
account asset disposal
disposal process
process disposal

Asset Disposal
Dispose Assets
Asset Transfer
Asset Disposal
Dispose Assets
Account Asset Disposal
Asset Maintenance
asset management
odoo asset
asset odoo
asset app
app asset
module asset
account_asset



            """,
    'author': 'Onnet Consulting Sdn Bhd, Probuse Consulting Service Pvt. Ltd.',
    'website': 'https://on.net.my/, http://www.probuse.com',
    'images': ['static/description/1.jpg'],
    'support': 'contact@probuse.com',
    'live_test_url': 'https://youtu.be/eQtrUG6t-QA',
    'depends': [
       'odoo_account_asset_extend_ce',
       'account_asset_disposal_ce',
       'th_asset_maintenance_ce',
       'odoo_asset_transfer_ce',
       'odoo_disposal_extend_ce',
   ],
    'data':[
        'views/account_asset_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
