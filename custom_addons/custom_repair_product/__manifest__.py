{
    'name': 'Productos para la reparación',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'summary': 'Gestión de productos asociados a órdenes de reparación',
    'description': """
    Este módulo permite gestionar de manera eficiente los productos que están asociados a órdenes de reparación.
    Incluye funcionalidades para rastrear el estado de los productos, gestionar su inventario y facilitar
    la creación de órdenes de trabajo.
    """,
    'category': 'Operations/Repair',
    'depends': [
        'repair',
        'product',
        'stock',
        'web_studio',
        'worksheet',
        'base',
    ],
    'data': [          
       'security/ir.model.access.csv',            
       'views/repair_product_views.xml',
       'views/repair_order_views.xml',
       'wizards/repair_worksheet_wizard_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
