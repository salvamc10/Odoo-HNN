{
    'name': "Vista de proyectos dividida por departamentos",
    'summary': "Sidebar de departamentos en proyectos como en el módulo de empleados",
    'description': """
    Este módulo añade una barra lateral de departamentos en la vista kanban de proyectos, similar a la que existe en empleados. 
    Permite filtrar proyectos por departamento, facilitando la gestión y visualización de proyectos relacionados con diferentes áreas de la empresa.
    Esta funcionalidad es especialmente útil para empresas que manejan múltiples proyectos y desean organizarlos por departamentos para una mejor visibilidad y gestión.
    """,
    'author': "Salva M",
    'category': 'Project',
    'version': '18.0.1.0',
    'license': 'LGPL-3',
    'depends': ['project', 'hr'],
    'data': [
        'views/project_views.xml',
    ],
    'installable': True,
    'application': False,
}
