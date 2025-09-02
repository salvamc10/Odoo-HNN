{
    'name': 'Dividir pedidos web por categoría',
    'version': '18.0.1.0',
    'author': 'Salva M',
    'license': 'LGPL-3',
    'summary': 'Divide el carrito en pedidos de Máquinas y Recambios usando categoría web',
    'description': 'Este módulo permite dividir los pedidos realizados en '
    'la tienda online en dos categorías: Máquinas y Recambios, facilitando así la gestión de los mismos.'
    'esto sirve para mejorar la organización y el control de los pedidos al separarlos por categoría.',
    'depends': ['website_sale', 'sale_management'],
    'data': [
        'views/website_settings_views.xml',
        'views/payment_provider_split_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
