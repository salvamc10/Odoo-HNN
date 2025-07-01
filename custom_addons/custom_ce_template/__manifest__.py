{
    'name': 'Hoja CE por producto en pedido de venta',
    'summary': 'Genera una hoja CE individual por producto o lote en cada pedido de venta',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'category': 'Sales/CRM',
    'depends': ['base''sale', 'stock'],
    'data': [
        'report/report_ce_document_stock_action.xml',
        'report/report_ce_document_stock.xml',
    ],
    'installable': True,
    'application': False,
}
