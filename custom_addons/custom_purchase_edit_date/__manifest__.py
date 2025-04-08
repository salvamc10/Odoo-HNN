{
    'name': 'Purchase: Editable Fecha Confirmación',
    'version': '1.0',
    'summary': 'Permite editar la fecha de confirmación en pedidos de compra',
    'description': """
    Este módulo permite editar la fecha de confirmación en los pedidos de compra.
    Se añade un campo editable en la vista de formulario del pedido de compra para modificar la fecha de confirmación.
    """,
    'category': 'Purchases',
    'license': 'LGPL-3',
    'author': 'Salva M',
    'depends': ['purchase'],
    'data': [
        'views/purchase_order_view.xml',
    ],
    'installable': True,
    'application': False,
}
