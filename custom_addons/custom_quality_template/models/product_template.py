from odoo import models, api # type: ignore

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._trigger_quality_sync()
        return records

    def _trigger_quality_sync(self):
        for rec in self:
            points = self.env['quality.point'].search([
                ('template_id', '!=', False),
                ('linked_operation_id', '=', False)
            ])
            for point in points:
                point._sync_linked_points()

    def write(self, vals):
        res = super().write(vals)
        if 'categ_id' in vals:
            for template in self:
                template._check_quality_points_auto()
                # Llamar también a nivel de variantes
                for variant in template.product_variant_ids:
                    variant._resync_quality_points_by_category()
        return res

    def _check_quality_points_auto(self):
        QualityPoint = self.env['quality.point']
        for rec in self:
            category_id = rec.categ_id.id
            product_variant_ids = rec.product_variant_ids.ids

            if not category_id or not product_variant_ids:
                continue

            # Buscar puntos base de plantillas que tengan esta categoría
            points = QualityPoint.search([
                ('product_category_ids', 'in', category_id),
                ('template_id', '!=', False),
                ('linked_operation_id', '=', False)
            ])

            for point in points:
                # Reforzamos seguridad para no duplicar
                for product in rec.product_variant_ids:
                    existing = QualityPoint.search([
                        ('origin_point_id', '=', point.id),
                        ('product_ids', 'in', product.id),
                        ('linked_operation_id', '!=', False),
                    ])
                    if not existing:
                        point._create_linked_points()
