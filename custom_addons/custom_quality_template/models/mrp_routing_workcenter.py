from odoo import models, fields, api # type: ignore

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    template_id = fields.Many2one('workcenter.operation.template', string="Plantilla de operación")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.template_id:
                for point in record.template_id.quality_point_ids:
                    point._create_linked_points()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'template_id' in vals:
            for record in self:
                if record.template_id:
                    for point in record.template_id.quality_point_ids:
                        point._create_linked_points()
        return res
    
    def copy(self, default=None):
        default = default or {}
        new = super().copy(default)

        QualityPoint = self.env['quality.point']

        # Eliminar cualquier punto arrastrado (copiado con el copy), clonado o no
        old_points = self.env['quality.point'].search([
            ('linked_operation_id', '=', new.id)
        ])
        old_points.unlink()


        # Generar nuevos solo si son necesarios y no existen para el producto
        if new.template_id:
            for point in new.template_id.quality_point_ids:
                point._create_linked_points()

        return new
