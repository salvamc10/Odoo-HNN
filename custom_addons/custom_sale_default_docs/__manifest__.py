{
    'name': 'Documentos por defecto en plantillas de presupuesto',
    'version': '18.0.1.0',
    'summary': 'Precarga automática de documentos obligatorios en pedidos según plantilla de presupuesto',
    'license': 'LGPL-3',
    'author': 'Salva M',
    'category': 'Sales',
    'depends': ['sale_pdf_quote_builder', 'sale_management'],
    'description': """
    Precarga automática de documentos obligatorios en pedidos según plantilla de presupuesto.
    
    Este módulo permite:
    - Definir en cada plantilla de presupuesto qué documentos son obligatorios y cuáles opcionales.
    - Cargar automáticamente en el pedido los documentos marcados como obligatorios al seleccionar la plantilla.
    - Mantener los opcionales disponibles para que el usuario pueda añadirlos manualmente.
    - Respetar la selección de documentos al generar el PDF o enviar el presupuesto.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/custom_quote_template_doc_views.xml',
        'views/sale_order_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
