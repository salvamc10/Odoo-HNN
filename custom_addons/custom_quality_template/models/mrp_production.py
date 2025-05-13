from odoo import models # type: ignore

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_quality_points(self):
        # Solo puntos que no están asociados a operaciones (es decir, manuales)
        points = super()._get_quality_points()
        return points.filtered(lambda p: not p.operation_id)