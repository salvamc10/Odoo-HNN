{
    'name': 'Hoja CE por producto en pedido de venta',
    'summary': 'Genera una hoja CE individual por producto o lote en cada pedido de venta',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'category': 'Sales/CRM',
    'depends': ['sale', 'stock'],
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
