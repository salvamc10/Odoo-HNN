{
    'name': 'Factura por tipo de venta',
    'summary': 'Asigna automáticamente una secuencia personalizada a facturas según la plantilla del pedido de venta.',
    'version': '1.0',
    'author': 'GrupoHNN',
    'website': 'https://www.grupohnn.com',
    'category': 'Contabilidad',
    'depends': ['account', 'sale'],
    'description': """
Este módulo asigna automáticamente una secuencia personalizada al crear una factura de cliente,
según la plantilla utilizada en el pedido de venta de origen.
    """,
    'data': [
        'data/ir_sequence_data.xml',
        'views/sequence_templates.xml'
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
