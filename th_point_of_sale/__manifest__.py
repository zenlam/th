{
    'name': 'TH - Point of Sale',
    'version': '12.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Point Of Sale',
    'description': """
TH - Point of Sale
==================
""",
    'website': 'https://on.net.my/',
    'depends': ['th_product_multi_uom', 'th_pos_lock_screen',
                'sale', 'web_widget_color'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',

        'views/templates.xml',
        'views/pos_category_views.xml',
        'views/pos_menu_category_views.xml',
        'views/pos_menu_modifier_views.xml',
        'views/pos_menu_views.xml',
        'views/pos_smart_select_views.xml',
        'views/pos_time_range_views.xml',
        'views/product_views.xml',
        'views/product_pricelist_views.xml',
        'views/pos_config_views.xml',
        'views/res_company_views.xml',
        'views/pos_order_views.xml',
        'views/store_management_views.xml',
        'views/pos_session_views.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
