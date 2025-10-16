{
    "name": "Desmontar y refabricar",
    "version": "18.0.1.0",
    "author": "Pedro M",
    "license": "LGPL-3",
    "summary": "Desmontar productos fabricados y refabricarlos",
    "description": """
    Este módulo permite seleccionar varias ordenes de fabricación , 
    desmontarlas y volverlas a fabricar con unas nuevas operaciones y componentes para su refabricacion.
    """,
    "category": "Manufacturing",
    "depends": ["mrp", "stock"],
    "data": [
        'views/mrp_production_views.xml',
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
