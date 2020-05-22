# -*- coding: utf-8 -*-
{
    'name': 'Delivery Carrier: MRW',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse',
    'author': "Punt Sistemes, S.L.U",
    'website': "https://odoo-community.org/",
    'depends': [
        'stock_picking_delivery_info_computation',
    ],
    'data': [
        'data/mrw_data.xml',
        'data/mrw_templates.xml',
        'views/delivery_carrier_view.xml',
        'views/stock_picking_view.xml',
        ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
