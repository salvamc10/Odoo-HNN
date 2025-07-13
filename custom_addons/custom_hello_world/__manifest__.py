{
    "name": "Hola Mundo",
    "version": "18.0.1.0",
    "author": "Salva M",
    "license": "LGPL-3",
    "summary": "Un módulo mínimo de ejemplo para probar el flujo de desarrollo",
    "description": """
    Este módulo añade un modelo muy simple llamado "Hello World"
    y lo muestra en el menú con vistas en lista y formulario.
    Sirve como base para probar la instalación y personalización de módulos.
    """,
    "category": "Tools",
    "depends": ["base"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "data": [
        "views/hello_world_view.xml"
    ]
}
