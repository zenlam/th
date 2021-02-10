# -*- coding: utf-8 -*-
# __author__ = 'Mitesh Savani'

{
    'name': 'Tim Hortons - Stock',
    'version': '1.0.1',
    'category': 'Warehouse',
    'sequence': 20,
    'summary': 'Manage your stock and logistics activities for Tim Hortons',
    'description': "",
    'depends': [
        'stock','purchase'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/stock_picking_view.xml',
        'views/stock_move_view.xml',
        'views/res_config_setting_views.xml',
        'wizard/stock_overprocessed_transfer_views.xml',
        'views/stock_inventory_view.xml',
        'views/stock_location_view.xml',
        'views/stock_move_line_views.xml',
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_request.xml',
        'views/damage_reason.xml',
        'views/scrap_picking.xml',
        'wizard/scrap_picking_warn_insufficient_qty.xml',
    ],
    'installable': True,
    'application': True,
    'website': 'https://on.net.my',
    'author': 'Onnet Consulting Sdn Bhd'
}
