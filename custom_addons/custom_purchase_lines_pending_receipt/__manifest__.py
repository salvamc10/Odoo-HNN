{
    "name": "Purchase Lines Pending Receipt",
    "version": "1.0",
    "depends": ["purchase", "stock"],
    "category": "Purchases",
    "author": "Pedro m.",
    'license': 'LGPL-3',
    "summary": "Vista de líneas de pedido pendientes de recepción",
    "description": "Agrega una vista de líneas de pedido donde la cantidad pedida es mayor a la recibida.",
    "data": [
        "views/purchase_lines_pending_view.xml"
    ],
    "installable": True,
    "application": False,
}
