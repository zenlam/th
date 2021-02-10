# -*- coding: utf-8 -*-
# __author__ = 'Mitesh Savani'

{
    'name': 'Tim Hortons - Product Expiry Date',
    'version': '1.0.1',
    'category': 'Product',
    'sequence': 20,
    'summary': 'Product expiry date',
    'description': """This module is only used to change the field type of product expiry/removal date.
                    This module should not contain any other changes except removal_date \n
                    as this module will uninstalled when user change the configuration for expiry date on inventory settings.
                    * Change the datatype for removal_date.
                    * Make removal date require in lot object.
                    """,
    'depends': [
        'product_expiry'
    ],
    'data': [
        'views/stock_move_view.xml'
    ],
    'installable': True,
    'application': True,
    'website': 'https://on.net.my',
    'author': 'Onnet Consulting Sdn Bhd'
}