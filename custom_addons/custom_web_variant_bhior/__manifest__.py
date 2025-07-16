{
    'name': 'Selección de variantes web',
    'version': '18.0.1.0',
    'summary': 'customiza la vista de las variantes de la web',
    'description': """
    Este módulo permite personalizar la vista de las variantes de productos con categoría recambios
    en la tienda online.
    """,
    'category': 'Website',
    'license': 'LGPL-3',
    'author': 'Pedro M',
    'depends': ['website_sale'],
    'data': [
        'views/product_template_inherit.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_web_variant_bhior/static/src/js/variant_selector.js',
                    ],
        'website.assets_frontend': [
            'custom_web_variant_bhior/static/src/js/variant_selector.js',
            
        ],
    },
    'installable': True,
    'application': False,
}
