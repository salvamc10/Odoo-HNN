from odoo import models, fields # type: ignore

class QualityPointTemplate(models.Model):
    _name = 'quality.point.template'
    _description = 'Plantilla puntos de calidad por categoría y centro'

    workcenter_id = fields.Many2one('mrp.workcenter', required=True, string='Centro de trabajo')
    categ_id = fields.Many2one('product.category', required=True, string='Categoría Producto')
    quality_point_ids = fields.Many2many('quality.point', string='Puntos de Control')
