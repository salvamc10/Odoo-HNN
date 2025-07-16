{
    'name': 'Botones y contadores de leads y oportunidades en contactos',
    'version': '18.0.1.0',
    'summary': 'Botones separados para Leads y Oportunidades desde contactos con sus respectivos contadores',
    'description': """
    Este módulo permite mostrar en el formulario de contactos dos botones separados:
    uno para oportunidades y otro para leads. Además, incluye contadores individuales
    para cada uno, sin interferir con el comportamiento estándar de Odoo.
    """,
    'category': 'Sales/CRM',
    'license': 'LGPL-3',
    'author': 'Salva M',
    'depends': ['crm'],
    'data': [
        'views/res_partner_view.xml',
        'views/res_partner_list_view.xml',
        'views/mail_activity_schedule_view_form_inherit.xml',
        'views/mail_activity_views.xml',
        'views/crm_lead_view.xml',
        'data/ir_rules.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
}
