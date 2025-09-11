{
    "name": "Gestión de garantías",
    "version": "18.0.1.0",
    "author": "Salva M",
    "license": "LGPL-3",
    "summary": "Gestión automática de garantías por número de serie desde ventas",
    "description": """
Este módulo permite seleccionar un periodo de garantía en meses desde el pedido de venta,
y propagar dicha información a los números de serie generados en la entrega.
Incluye fecha de inicio y fin de garantía para cada lote/serie.
""",
    "category": "Sales",
    "depends": ["sale_management", "stock"],
    "data": [
        "views/stock_lot_view.xml",
        "views/sale_order_view.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
