# -*- coding: utf-8 -*-
from odoo import models, api # type: ignore

"""
Este módulo extiende el modelo de Quality Point para permitir la asignación de puntos de control a centros de trabajo específicos.
"""

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for production in records:
            production._generate_quality_checks_by_category_and_workcenter()
        return records

    def _generate_quality_checks_by_category_and_workcenter(self):
        """Genera quality.checks por categoría de producto y centro de trabajo (workcenter_id), si no se define operación."""
        self.ensure_one()
        QualityCheck = self.env['quality.check']
        Product = self.product_id
        Categories = Product.categ_id

        points = self.env['quality.point'].search([
            ('product_category_ids', '!=', False),
            ('workcenter_id', '!=', False),
            ('operation_id', '=', False)
        ])

        for workorder in self.workorder_ids:
            for point in points:
                if (
                    point.workcenter_id == workorder.workcenter_id and
                    Categories in point.product_category_ids
                ):
                    QualityCheck.create({
                        'workorder_id': workorder.id,
                        'production_id': self.id,
                        'point_id': point.id,
                        'team_id': point.team_id.id,
                        'company_id': self.company_id.id,
                        'product_id': self.product_id.id,
                    })
