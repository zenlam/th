# -*- coding: utf-8 -*-

{
    'name': 'TH Landed Cost',
    'version': '12.0.1.0.0',
    'author': 'Onnet Solution SDN BHD',
    'website': 'http://www.onnet.my',
    'depends': ['stock', 'stock_landed_costs'],
    'description': """
Tim Hortons Landed Cost
===================    
    """,
    'data': [
        'views/purchase_order.xml',
        'views/res_config_settings.xml',
        'views/res_partner.xml',
        'views/stock_landed_cost.xml',
        'views/stock_picking.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'installable': True,
}
