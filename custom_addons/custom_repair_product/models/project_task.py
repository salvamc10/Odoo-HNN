from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = "project.task"

    def _get_project_task_manager_group(self):
        return "project.group_project_manager"
