# -*- coding: utf-8 -*-
# __author__ = 'trananhdung'

{
    'name': 'Tim Hortons - Product UOM Management',
    'version': '1.0.1',
    'category': 'product',
    'sequence': 20,
    'summary': 'Manage multiple UoMs for Tim Hortons\'s product',
    'description': "",
    'depends': [
        'point_of_sale',
        'purchase',
        'th_asset',
    ],
    'data': [
        'views/product_multi_uom.xml',
        'views/product_product_view.xml',
        'views/product_template_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
    'website': '',
    'author': 'longdt'
}
