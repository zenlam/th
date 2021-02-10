# -*- coding: utf-8 -*-
# __author__ = 'minhld'

{
    'name': 'Tim Hortons - Product Management',
    'version': '1.0.1',
    'category': 'Master Data',
    'sequence': 20,
    'summary': '',
    'description': "",
    'depends': [
        'th_base',
        'product',
    ],
    'data': [
        'security/security.xml',
        'security/groups.xml',
        'views/product.xml',
        'views/product_supplier_info.xml'
    ],
    'installable': True,
    'application': True,
    'website': 'http://erp.net.vn',
    'author': 'Onnet Consulting VN JSC'
}
