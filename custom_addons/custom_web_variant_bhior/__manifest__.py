{
    'name': 'Web Variant Selector BHior',
    'version': '18.0.1.0',
    'summary': 'customiza la vista de las variantes de la web',
    'description': """
    Este módulo permite personalizar la vista de las variantes de productos con categoría recambios
    en la tienda online.
    """,
    'category': 'Website',
    'license': 'LGPL-3',
    'author': 'Pedro M',
    'depends': ['website_sale', 'product'],
    'data': [
        'views/templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_web_variant_bhior/static/src/js/variant_selector.js', 
            # 'custom_web_variant_bhior/static/src/xml/template_view.xml'                      
        ],
    },
    'installable': True,
    'application': False,
}
