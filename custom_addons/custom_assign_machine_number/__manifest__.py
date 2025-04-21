# -*- coding: utf-8 -*-
{
    'name': 'Asignación de número de máquina',
    'summary': 'Asigna un número de máquina automático excepto para la categoría "Recambios / Bhior"',
    'description': '''
    Este módulo reemplaza una automatización de Odoo Studio.  
    Asigna automáticamente un número de máquina mediante una secuencia personalizada,  
    salvo si el producto pertenece a la categoría "Recambios / Bhior".
    ''',
    'author': 'Salva M',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'data': [],
    'installable': True,
    'application': False,
}
