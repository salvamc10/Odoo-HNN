from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    total_operation_count = fields.Integer(
        string="Total Operaciones Activas",
        compute="_compute_total_operation_count",
        store=False
    )

    @api.depends('workorder_ids.state')
    def _compute_total_operation_count(self):
        for record in self:
            active_workorders = record.workorder_ids.filtered(
                lambda w: w.state not in ('done', 'cancel')
            )
            record.total_operation_count = len(active_workorders)
