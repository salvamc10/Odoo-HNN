{
    'name': "Sincronización de Email con Mailing List",
    'version': '18.0.1.0.0',
    'summary': "Automatiza la incorporación y actualización de contactos en la lista de mailing a partir de los registros en res.partner.",
    'description': """
        Este módulo añade la funcionalidad para que:
            - Al crear un contacto (res.partner) que incluya un correo, se agregue automáticamente un registro en la lista de mailing "BBDD BHIOR BASE DE DATOS ESPAÑA".
            - Al editar el campo email en el contacto, se actualice el correo en el registro asociado de mailing.contact.
            
        Se previene duplicidad mediante la asignación de un campo relacional.
    """,
    'author': "Tu Nombre",
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
