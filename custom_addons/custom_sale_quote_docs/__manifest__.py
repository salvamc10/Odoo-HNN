{
    "name": "Adjuntos automáticos por plantilla de presupuesto",
    "version": "18.0.1.0",
    "author": "Salva M",
    "license": "LGPL-3",
    "summary": "Adjuntos obligatorios/opcionales automáticamente en presupuestos y pedidos",
    "description": "Este módulo permite adjuntar documentos automáticamente a los presupuestos y "
    "pedidos basándose en la plantilla seleccionada."
    "Esto es útil para garantizar que los documentos necesarios estén siempre adjuntos.",
    "depends": ["sale_management", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_template_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
