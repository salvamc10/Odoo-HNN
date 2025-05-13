from odoo import models # type: ignore

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def unlink(self):
        QualityPoint = self.env['quality.point']
        product_ids = []
        for bom in self:
            product_ids += bom.product_tmpl_id.product_variant_ids.ids

        # Borrar puntos asociados a esos productos
        points = QualityPoint.search([
            ('product_ids', 'in', product_ids)
        ])
        points.unlink()

        return super().unlink()
