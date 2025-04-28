# -*- coding: utf-8 -*-
{
    'name': 'Asignación de número de máquina',
    'summary': 'Asigna un número de máquina a todos los productos que pertenecen a las categorías declaradas', 
    'description': '''
    Este módulo reemplaza una automatización de Odoo Studio.  
    Asigna automáticamente un número de máquina mediante una secuencia personalizada, a todos los productos que pertenecen a las categorías declaradas.
    Es importante que la secuencia personalizada esté configurada correctamente para evitar problemas de duplicación de números de máquina.
    El nombre técnico de la secuencia personalizada es 'machine.sequence'.
    ''',
    'author': 'Salva M',
    'version': '18.0.1.0',
    'category': 'Warehouse',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'data': [],
    'installable': True,
    'application': False,
}
