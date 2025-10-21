{
    'name': "Sincronización de email del contacto con Mailing List",
    'version': '18.0.1.0',
    'summary': "Automatiza la incorporación y actualización de contactos en listas de mailing según compañía y provincia.",
    'description': """
    Este módulo añade la funcionalidad para que:
        - Al crear o modificar un contacto (res.partner), se agregue automáticamente a las listas de mailing correspondientes según su compañía y provincia.
        - Al editar el campo email, compañía o provincia, se actualice la asignación de listas automáticamente.
        - Solo se importa el email, sin nombre u otros datos del contacto.
        
    Reglas de asignación:
        - Compañía ID 1: Lista ID 2
        - Compañía ID 2:
            * Provincia 420 o 451: Lista ID 12
            * Provincia 421: Lista ID 13
            * Provincia 419: Lista ID 14
            * Otras provincias: No asignado a ninguna lista
        - Compañía ID 6: Lista ID 78 (sin importar provincia)
        - Otras compañías: No asignado a ninguna lista
    
    Se previene duplicidad mediante la asignación de un campo relacional.
    """,
    'author': "Salva M",
    'category': 'Marketing',
    'license': 'LGPL-3',
    'depends': [
        'mass_mailing',
        'contacts', 
    ],
    'data': [
        
    ],
    'installable': True,
    'application': False,
}
