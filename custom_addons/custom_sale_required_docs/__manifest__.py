{
    'name': 'Documentos obligatorios en plantillas de presupuesto',
    'version': '18.0.1.0',
    'summary': 'Marca documentos obligatorios por plantilla y precárgalos en el pedido',
    'license': 'LGPL-3',
    'author': 'Salva M',
    'category': 'Sales',
    'depends': ['sale_pdf_quote_builder', 'sale_management'],
    'description': """
    Permite seleccionar, por plantilla de presupuesto, qué documentos del creador de presupuestos
    son obligatorios. Al elegir la plantilla en el pedido, se marcan solo esos.
    Aún así, los no obligatorios pero relevantes se pueden seleccionar manualmente.
    """,
    'data': [
        'views/sale_order_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
