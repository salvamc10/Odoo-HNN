from odoo import models # type: ignore

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super().write(vals)
        if 'categ_id' in vals:
            for product in self:
                product._resync_quality_points_by_category()
        return res

    def unlink(self):
        QualityPoint = self.env['quality.point']
        for product in self:
            points = QualityPoint.search([
                ('product_ids', 'in', product.id)
            ])
            points.unlink()
        return super().unlink()

    def _resync_quality_points_by_category(self):
        QualityPoint = self.env['quality.point']
        for rec in self:
            # 1. Eliminar puntos que ya no aplican
            points_to_remove = QualityPoint.search([
                ('product_ids', 'in', rec.id),
                ('origin_point_id.product_category_ids', '!=', False)
            ])
            for point in points_to_remove:
                expected_categs = point.origin_point_id.product_category_ids.ids
                if rec.categ_id.id not in expected_categs:
                    point.unlink()

            # 2. Crear nuevos puntos si aplica la nueva categoría
            matching_templates = QualityPoint.search([
                ('template_id', '!=', False),
                ('linked_operation_id', '=', False),
                ('product_category_ids', 'in', rec.categ_id.id)
            ])
            for point in matching_templates:
                point._create_linked_points()
