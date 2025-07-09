{
    'name': "Vista de proyectos con departamentos",
    'summary': "Sidebar de departamentos en proyectos como en empleados/contactos",
    'description': """
    Este módulo añade una barra lateral de departamentos en la vista kanban de proyectos, similar a la que existe en empleados y contactos. 
    Permite filtrar proyectos por departamento, facilitando la gestión y visualización de proyectos relacionados con diferentes áreas de la empresa.
    """,
    'author': "Salva M",
    'category': 'Project',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'depends': ['project', 'hr', 'project', 'project_enterprise'],
    'data': [
        'views/project_views.xml',
        'views/project_kanban.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
