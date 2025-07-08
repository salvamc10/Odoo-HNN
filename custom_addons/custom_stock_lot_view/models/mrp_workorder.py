from odoo import models, fields, api
from odoo import exceptions

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

   
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            if 'production_id' in vals:
                production = self.env['mrp.production'].browse(vals['production_id'])
                if production.lot_producing_id:
                    record.finished_lot_id = production.lot_producing_id.id
        return records

    def button_finish(self):
            for workorder in self:
                # Buscar checks de calidad pendientes
                checks = self.env['quality.check'].search([
                    ('workorder_id', '=', workorder.id),
                    ('point_id', '!=', False)
                ])
                checks_fallidos = checks.filtered(lambda c: c.quality_state != 'pass')

                # Buscar alertas asociadas
                alertas = self.env['quality.alert'].search([
                    ('workorder_id', '=', workorder.id)
                ])

                if checks_fallidos and not alertas:
                    raise exceptions.UserError(
                        "⚠️ No se puede finalizar la operación.\n"
                        "Hay controles de calidad sin aprobar y no se ha registrado ninguna alerta de calidad que lo justifique."
                    )


            return super().button_finish()