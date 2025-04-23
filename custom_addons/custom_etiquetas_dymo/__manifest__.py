{
    "name": "Etiquetas 54x25 mm para impresora DYMO",
    "summary": "Agrega la opción de imprimir etiquetas de número de serie en formato 54x25 mm (PDF)",
    "description": """ Este módulo permite imprimir etiquetas de número de serie en formato 54x25 mm (PDF) para impresoras DYMO.
    Se puede acceder a esta opción desde el menú de inventario, en la sección de etiquetas de productos.
    """,
    "license": "AGPL-3",
    "version": "18.0.1.0",
    "author": "Salva M",
    "category": "Inventory",
    "depends": ["stock", "stock_barcode", "stock_barcode_labels", "base"],
    "data": [
        "report/report_label_54x25.xml",
        "report/report.xml",
        "data/label_formats.xml"
    ],
    "installable": True,
    "application": False
}