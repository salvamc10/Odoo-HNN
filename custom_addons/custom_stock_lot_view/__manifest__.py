# -*- coding: utf-8 -*-
{
    'name': "Vista para la fabricación de productos",
    'version': '18.0.1.0',
    'author': "Salva M",
    'category': 'Inventory',
    'summary': 'Vista personalizada para la fabricación de productos con número de serie',
    'description': """
    Vista completa para la fabricación de productos con número de serie.
    Permite ver los números de serie de los productos fabricados y su estado en la fabricación.
    Así como el mecánico responsabe, el modelo en cuestión y demás campos.
    """,
    'depends': ['stock', 'product', 'mrp', 'custom_lot_labels'],
    'data': [
        'views/stock_lot_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
