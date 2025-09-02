{
    'name': 'Gestión de firmas de correo por compañía',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Gestión de firmas de correo por compañía',
    'description': """
        Este módulo permite a los usuarios tener diferentes firmas de correo para cada compañía.
        
        Características:
        ---------------
        * Crea automáticamente campos de firma para cada compañía
        * Permite personalizar la firma por compañía para cada usuario
        * Inserta automáticamente la firma correcta según la compañía activa
        * Se integra con el sistema de correo de Odoo
        
        Uso:
        ----
        1. Al crear una nueva compañía, se crea automáticamente un campo de firma para esa compañía
        2. Los usuarios pueden configurar sus firmas específicas para cada compañía
        3. Al enviar correos, se usa automáticamente la firma correspondiente a la compañía activa
    """,
    'author': 'Pedro M.',
    'website': 'https://www.bhior.com',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/res_company_views.xml',
        'views/mail_template_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_signature_mail_for_company/static/src/js/signature_field.js',
            'custom_signature_mail_for_company/static/src/xml/signature_field.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
