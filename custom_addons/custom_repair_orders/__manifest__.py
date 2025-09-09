{
    'name': 'Reparaciones por número de serie/máquina',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'summary': 'Gestión de reparaciones asociadas a productos por número de serie/máquina',
    'description': """
    Este módulo permite gestionar de manera eficiente las reparaciones asociadas a productos específicos
    mediante el uso de números de serie o identificadores de máquina. Facilita el seguimiento del estado
    de las reparaciones y mejora la organización del proceso de reparación.
    """,
    'category': 'Inventory/Repairs',
    'depends': ['repair', 'stock'],
    'data': [
        'views/repair_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
