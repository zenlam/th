# -*- coding: utf-8 -*-
# __author__ = 'trananhdung'

{
    'name': 'Tim Hortons - EDI API',
    'version': '1.0.1',
    'category': 'Tools',
    'sequence': 15,
    'summary': '',
    'description': "",
    'depends': [
        'base_setup'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/edi_log.xml',
        'views/settings.xml',
    ],
    'installable': True,
    'application': True,
    'website': 'http://erp.net.vn',
    'author': 'Onnet Consulting VN JSC'
}
