# -*- coding: utf-8 -*-
# __author__ = 'trananhdung'

{
    'name': 'Tim Hortons - Outlet Ordering Management',
    'version': '1.0.1',
    'category': 'Inventory',
    'sequence': 20,
    'summary': '',
    'description': "",
    'depends': [
        'th_outlet',
        'th_purchase_requisition',
        'th_product_multi_uom',
        'th_stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'data/sequence.xml',
        'data/location.xml',
        'data/picking_type.xml',
        'data/cron.xml',
        'views/menu.xml',
        'views/delivery_cycle.xml',
        'views/ordering_history_template.xml',
        'views/outlet.xml',
        'views/product.xml',
        'views/outlet_product_deny.xml',
        'views/ordering_template.xml',
        'views/ordering.xml',
        'views/stock.xml',
        'views/settings.xml',
    ],
    'installable': True,
    'application': True,
    'website': 'http://erp.net.vn',
    'author': 'Onnet Consulting VN JSC'
}
