{
    "name": "Documentos adjuntos por defecto en presupuestos/pedidos",
    "version": "18.0.1.0",
    "author": "Salva M",
    "license": "LGPL-3",
    "summary": "Este módulo permite adjuntar documentos por defecto en presupuestos y pedidos.",
    "description": "Este módulo añade la funcionalidad de adjuntar documentos de forma predeterminada "
    "en los presupuestos y pedidos de venta. "
    "De forma que, al crear un nuevo presupuesto o pedido, los documentos seleccionados se adjunten automáticamente.",
    "depends": ["sale_pdf_quote_builder", "sale_management"],
    "data": [
        "views/sale_order_template_views.xml"
    ],
    "installable": True
}
