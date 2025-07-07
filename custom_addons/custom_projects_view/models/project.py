from odoo import fields, models

class ProjectProject(models.Model):
    _inherit = "project.project"

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        required=True,
        index=True,
        default=lambda self: self.env['hr.department'].search([], limit=1).id,
        ondelete='restrict',
    )
