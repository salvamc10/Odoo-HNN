# -*- coding: utf-8 -*-
{
    'name': 'Proyectos por departamento predefinidos',
    'author': 'Salva M',
    'version': '18.0.1.0',
    'category': 'Project',
    'summary': 'Pantalla inicial por Departamento > Proyecto > Tareas',
    'depends': ['project', 'hr'],
    'data': [
        'views/hr_department_kanban.xml',
        'views/project_filtered_by_department.xml',
        'views/task_filtered_by_project.xml',
        'views/menu_items.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
