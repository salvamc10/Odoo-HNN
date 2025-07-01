{
    'name': 'Hoja CE por producto en pedido de venta',
    'summary': 'Genera una hoja CE individual por producto o lote en cada pedido de venta',
    'version': '18.0.1.0',
    'author': 'Pedro M',
    'license': 'LGPL-3',
    'category': 'Sales/CRM',
    'depends': ['sale', 'stock'],
    'data': [
        'report/ce_report_action_stock.xml',
        'report/ce_report_template_stock.xml',        
    ],
    'installable': True,
    'application': False,
}
