# -*- coding: utf-8 -*-
# __author__ = 'trananhdung'

{
    'name': 'Tim Hortons - Outlet Management',
    'version': '1.0.1',
    'category': 'Point Of Sale',
    'sequence': 20,
    'summary': '',
    'description': "",
    'depends': [
        'th_base',
        'th_product',
        'purchase_stock',
        'point_of_sale'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        # 'views/stock_warehouse_view.xml',
        'views/store_management_view.xml',
        'views/res_area.xml',
        'views/pos_config_view.xml',
        # 'views/product.xml',
        'views/res_user_view.xml',
        'views/stock_warehouse_view.xml',
        # 'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,
    'website': 'http://erp.net.vn',
    'author': 'Onnet Consulting VN JSC'
}
