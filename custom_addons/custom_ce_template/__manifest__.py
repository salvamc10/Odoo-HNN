{
    'name': 'Hoja CE y manual por producto en factura',
    'summary': 'Genera una hoja CE individual por producto o lote junto con su manual en cada factura',
    'description': """
    Este módulo permite generar una hoja CE individual por cada producto o lote en las facturas,
    incluyendo un manual específico para cada producto. La hoja CE se adjunta como un documento PDF
    en la factura, facilitando el cumplimiento de normativas y la entrega de información relevante al
    cliente.
    """,
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'category': 'Sales/CRM',
    'depends': ['base', 'sale', 'stock', 'web', 'account', 'product'],
    "data": [
        "report/ir_actions_report_templates.xml",
        "report/ir_actions_report.xml",
    ],
    'assets': {
        'web.report_assets_common': [
            'custom_ce_template/static/src/img/bhior.jpg',
            'custom_ce_template/static/src/img/bhior2.jpg',
        ],
    },
    'installable': True,
    'application': False,
}
