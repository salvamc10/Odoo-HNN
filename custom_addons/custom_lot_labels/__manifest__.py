{
    'name': 'Etiquetas personalizadas para números de serie/lote',
    'version': '18.0.1.0',
    'summary': 'Impresión de etiquetas Dymo y A4 para números de serie o lote',
    'license': 'LGPL-3',
    'author': 'Salva M',
    'category': 'Inventory',
    'depends': ['stock', 'hr_payroll'],
    'description': """
    Impresión de etiquetas Dymo y A4 para números de serie o lote.
    Este módulo permite imprimir etiquetas personalizadas para números de serie o lote en formato Dymo y A4.
    Las etiquetas pueden incluir información como el nombre del producto, el número de serie o lote, y otros detalles relevantes.
    Para utilizar las dimensiones correctas de las etiquetas Dymo en este módulo, es necesario modificarlo manualmente:
    - Ancho de página: **25 mm**
    - Alto de página: **45 mm**
    - Márgenes: **0 mm** en todos los lados
    - Orientación: **Landscape**
    """,
    'data': [
        'report/lot_label_A4_report.xml',
        'report/label_dymo_remove_price.xml',
        'report/label_dymo_fix_default_code.xml',
        'report/label_dymo_lot.xml',
    ],
    'installable': True,
    'application': False,
}


