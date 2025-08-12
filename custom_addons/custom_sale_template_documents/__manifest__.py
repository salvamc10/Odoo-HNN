{
    'name': 'Adjuntos automáticos de plantilla en presupuestos/pedidos',
    'version': '18.0.1.0',
    'author': 'Salva M',
    'license': 'LGPL-3',
    'summary': 'Adjunta documentos de plantilla automáticamente en presupuesto y/o pedido',
    'description': """
    Automatiza el adjuntado de documentos definidos en la plantilla de presupuesto.
    Dos modos por documento:
    - Adjuntar siempre al crear presupuesto.
    - Adjuntar siempre al confirmar pedido.
    Se mantiene la selección manual existente para el resto.
    """,
    'category': 'Sales',
    'depends': ['sale_management', 'sale_pdf_quote_builder'],
    'data': [
        'views/sale_order_template_document_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
