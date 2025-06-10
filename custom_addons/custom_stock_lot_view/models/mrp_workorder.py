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

   
    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'production_id' in vals:
            production = self.env['mrp.production'].browse(vals['production_id'])
            if production.lot_producing_id:
                res.finished_lot_id = production.lot_producing_id.id
        return res
