from odoo import models, fields # type: ignore

class WorkcenterOperationTemplate(models.Model):
    _name = 'workcenter.operation.template'
    _description = 'Plantilla de Operación de Trabajo'

    name = fields.Char(required=True)
    quality_point_ids = fields.One2many('quality.point', 'template_id', string="Puntos de control")
    operation_ids = fields.One2many('mrp.routing.workcenter', 'template_id', string="Operaciones asociadas")
