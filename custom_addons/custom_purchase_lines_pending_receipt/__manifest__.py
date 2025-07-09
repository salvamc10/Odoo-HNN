{
    'name': 'Líneas de compra pendientes de recepción',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'summary': 'Vista de líneas de pedido donde la cantidad pedida supera la recibida',
    'description': """
    Este módulo agrega una vista personalizada que muestra las líneas de pedido de compra
    en las que la cantidad pedida es mayor a la cantidad ya recibida.
    Facilita la gestión de recepciones pendientes en almacén.
    """,
    'category': 'Purchases',
    'depends': ['purchase', 'stock'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'views/purchase_lines_pending_view.xml',
    ],
}
