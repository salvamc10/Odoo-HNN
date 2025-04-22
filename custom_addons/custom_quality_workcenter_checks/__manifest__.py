{
    'name': 'Checks automáticos por Categoría y Centro',
    'version': '1.0',
    'summary': 'Automatiza asignación de checks de calidad según categoría y centro de trabajo',
    'description': 'Asigna automáticamente puntos de control a órdenes de trabajo según categoría de producto y centro de trabajo.',
    'category': 'Manufacturing',
    'author': 'Salva M',
    'depends': ['mrp', 'quality'],
    'data': [
        'views/quality_point_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
