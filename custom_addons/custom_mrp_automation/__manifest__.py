# -*- coding: utf-8 -*-
{
    'name': 'Órdenes de fabricación automáticas',
    'version': '18.0.1.0.0',
    'summary': 'Automatiza la creación de órdenes de fabricación tras validar recepciones',
    'description': """
    Este módulo permite automatizar la creación de órdenes de fabricación en Odoo 18
    después de validar las recepciones de productos. Facilita la gestión de la producción
    al generar automáticamente las órdenes de fabricación necesarias basadas en las recepciones validadas.
    Permite una integración más fluida entre la gestión de inventario y la producción, mejorando la eficiencia del proceso.
    """,
    'author': 'Pedro M.',
    'website': '',
    'category': 'Manufacturing',
    'depends': ['mrp', 'stock'],
    "data": [        
    ],    
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
