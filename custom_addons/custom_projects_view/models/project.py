from odoo import fields, models

class ProjectProject(models.Model):
    _inherit = "project.project"

    department_id = fields.Many2one(
        'hr.department',
        string="Departamento",
        required=True,
        help="Departamento responsable del proyecto."
    )
