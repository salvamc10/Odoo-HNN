{
    'name': 'Custom Funcional',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'summary': 'Módulo para funcionalidades personalizadas',
    'description': """
    Este módulo proporciona funcionalidades personalizadas para la implementación 
    específica del cliente.
    """,
    'category': 'Custom',
    'depends': ["web", "mail"],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_funcional/static/src/js/*.js',            
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
