# -*- coding: utf-8 -*-
{
    'name': 'Creación Automática de Cuentas Analíticas y Distribución',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Purchases',
    'summary': 'Módulo para crear automáticamente cuentas analíticas por números de serie/lote en recepciones de compra y distribuir analíticamente las líneas de compra.',
    'description': """
        Implementa dos historias de usuario:
        - HU1: Creación automática de cuentas analíticas al validar recepciones con series/lotes (solo compañía ID=2).
        - HU2: Distribución automática equitativa en purchase.order.line basada en qty por lote.
        
        Dependencias: purchase, stock, account.
        Incluye pruebas unitarias.
    """,
    'author': 'Pedro M',
    'website': 'https://github.com/mayorGonzalez/grupohnn-odoo-hnn-custom-cuentas-analiticas',  # Ajusta a tu repo
    'license': 'LGPL-3',
    'depends': [
        'purchase',
        'stock',
        'account',
    ],
    'data': [        
    ],    
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {},  
}