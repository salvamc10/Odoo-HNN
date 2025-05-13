from odoo import models  # type: ignore

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def _get_quality_points(self):
        product = self.production_id.product_id
        points = super()._get_quality_points()

        # Aplicar filtrado forzado a todos, aunque estén asignados por operation_id
        return points.filtered(lambda p: (
            (not p.product_ids or product.id in p.product_ids.ids) and
            (not p.product_category_ids or product.categ_id.id in p.product_category_ids.ids)
        ))

    def mark_quality_check_passed(self, quality_point_id):
        """Valida automáticamente el quality.check asociado a un punto de control específico."""
        self.ensure_one()
        QualityCheck = self.env['quality.check']

        check = QualityCheck.search([
            ('workorder_id', '=', self.id),
            ('point_id', '=', quality_point_id),
            ('state', '!=', 'pass'),
        ], limit=1)

        if check:
            check.do_pass()
        return True
