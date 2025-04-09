{
    'name': 'Quality Control by Workcenter',
    'version': '1.0',
    'category': 'Manufacturing',
    'author': 'Salva M',
    'summary': 'Permite aplicar puntos de control por centro de trabajo',
    'description': '''
Este módulo extiende la funcionalidad de control de calidad en Odoo para permitir asignar puntos de control a centros de trabajo específicos.
Permite aplicar controles sin necesidad de definirlos por producto o categoría de producto, facilitando así un control más preciso en entornos con líneas de producción definidas por centro.
''',
    'depends': ['quality_control', 'mrp'],
    'data': [
        'views/quality_point_views.xml',
    ],
    'installable': True,
    'application': False,
}
