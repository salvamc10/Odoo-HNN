{
    'name': 'custom_repair_product_search_lot_serial',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'summary': 'Búsqueda de producto en reparaciones por número de lote/serie o numero de máquina',
    'description': """
    Este módulo personaliza el proceso de búsqueda de productos
    dentro de las órdenes de reparación. En lugar de usar el ID de
    la máquina, permite localizar el producto asociado a través de
    su número de lote/número de serie o número de máquina.
    
    Modelos afectados:
    - repair.order
    - stock.production.lot
    
    Ventajas:
    - Agiliza la identificación del producto en reparaciones.
    - Evita dependencias del ID de máquina.
    - Refuerza la trazabilidad mediante lotes y números de serie.
    """,
    'category': 'Services/Repair',
    'depends': [
        'repair',
        'stock',
    ],
    'data': [
        
        'views/repair_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
