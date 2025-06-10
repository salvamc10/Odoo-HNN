from odoo import models, fields, api

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    operation_count = fields.Integer(
        string="Operaciones Activas",
        compute="_compute_operation_count",
        store=True
    )

    @api.depends('production_id.workorder_ids.state')
    def _compute_operation_count(self):
        for record in self:
            active_workorders = record.production_id.workorder_ids.filtered(
                lambda w: w.state not in ('done', 'cancel')
            )
            record.operation_count = len(active_workorders)
