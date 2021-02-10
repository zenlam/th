# -*- coding: utf-8 -*-
# __author__ = 'trananhdung'

{
    'name': 'Tim Hortons - Stock Recall by HQ',
    'version': '1.0.1',
    'category': 'stock',
    'sequence': 20,
    'summary': '',
    'description': "",
    'depends': [
        'th_outlet_ordering',
        'product_expiry'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/recall.xml',
        'views/recall_picking.xml'
    ],
    'installable': True,
    'application': True,
    'website': '',
    'author': 'longdt'
}
