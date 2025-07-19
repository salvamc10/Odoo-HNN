{
    'name': 'Asignación automática de número de máquina',
    'version': '18.0.1.0',
    'author': 'Salva M',
    'license': 'LGPL-3',
    'summary': 'Asigna un número de máquina con formato personalizado usando una secuencia',
    'description': """
    Este módulo asigna automáticamente un número de máquina a los lotes (números de serie)
    cuando se crean, usando una secuencia con prefijo "B" y formato de 6 dígitos.
    Solo se aplica a productos en categorías válidas.
    """,
    'category': 'Inventory/Stock',
    'depends': ['stock', 'mrp'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'data/ir_sequence.xml',
        'views/stock_production_lot_views.xml',
    ],
}
