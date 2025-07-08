{
    'name': 'Diferencia con stock mínimo en productos',
    'version': '18.0.1.0',
    'author': 'Salva M',
    'license': 'LGPL-3',
    'summary': 'Campo calculado que indica cuántas unidades faltan para llegar al stock mínimo del producto',
    'description': """
    Este módulo añade un campo calculado en productos que muestra cuántas unidades faltan
    para alcanzar el stock mínimo configurado en las reglas de reabastecimiento.
    Permite filtrar fácilmente los productos que están por debajo del mínimo deseado.
    """,
    'category': 'Inventory/Stock',
    'depends': ['stock'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'views/product_template_views.xml',
    ],
}
