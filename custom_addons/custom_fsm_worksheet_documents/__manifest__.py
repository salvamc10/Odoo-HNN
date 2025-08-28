{
    'name': 'FSM Worksheet Documents Integration',
    'version': '18.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Integrate FSM worksheets with documents module',
    'description': """
        Este módulo extiende la funcionalidad de las hojas de trabajo del servicio de campo para:
        - Permitir la firma digital de las hojas de trabajo
        - Almacenar automáticamente en el módulo de documentos
        - Organizar las hojas de trabajo en carpetas específicas
        - Gestionar plantillas personalizadas con firma
    """,
    'author': 'Pedro M',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'industry_fsm',
        'documents',
        'web_signature',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fsm_worksheet_template_views.xml',
        'views/project_task_views.xml',
        'views/worksheet_document_folder_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
