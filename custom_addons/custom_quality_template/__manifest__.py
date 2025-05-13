{
    'name': 'Plantillas para controles de calidad',
    'summary': 'Plantillas creadas para estandarizar operaciones de calidad',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'description': """
    Este módulo permite crear plantillas para controles de calidad en Odoo.
    Las plantillas estandarizan operaciones y aseguran el seguimiento uniforme de procedimientos en toda la empresa.
    Tipos de controles soportados:
    - Generales: Se aplican a todos los productos.
    - Por categorías/as: Se aplican a productos de una categoría específica.
    - Por productos: Se aplican a productos específicos.
    """,
    'author': 'Salva M',
    'category': 'Manufacturing',
    'depends': ['mrp', 'quality', 'quality_control'],
    'data': [
        'security/ir.model.access.csv',
        'views/quality_point_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
