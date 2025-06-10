from odoo import fields, models

class ProjectProject(models.Model):
    _inherit = "project.project"

    department_id = fields.Many2one(
        'hr.department',
        string="Departamento",
<<<<<<< HEAD
        required=True,
=======
>>>>>>> 7b39f473d48bb166860e6c406b057bf11508deb8
        help="Departamento responsable del proyecto."
    )
