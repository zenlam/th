# -*- coding: utf-8 -*-
# __author__ = 'Mitesh Savani'

{
    'name': 'Tim Hortons - Purchase Requisition',
    'version': '1.0.1',
    'category': 'Purchase',
    'summary': 'Purchase Requisition ',
    'description': """
                    """,
    'depends': [
            'th_outlet', 'th_stock', 'th_purchase_multi_uom'
    ],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/delivery_cycle.xml',
        'views/purchase_requisition_template_view.xml',
        'views/purchase_request_template_view.xml',
        'views/product_view.xml',
        'views/purchase_request_view.xml',
        'views/purchase_view.xml',
        'wizard/wizard_po_line_delete_view.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': True,
    'website': 'https://on.net.my',
    'author': 'Onnet Consulting Sdn Bhd'
}
