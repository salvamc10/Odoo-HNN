# -*- coding: utf-8 -*-
from odoo import models, api  # type: ignore

"""
Este módulo extiende el modelo de mrp.production para generar automáticamente quality.checks
en función de los puntos de control definidos por producto, categoría o de forma general,
siempre que coincidan con el centro de trabajo de la operación.

Casos contemplados:
1. Punto de control por producto específico (product_id)
2. Punto de control por categoría de producto (product_category_ids)
3. Punto de control común a todos los productos (sin producto ni categoría)

En todos los casos, se requiere que el centro de trabajo del punto coincida
con el centro de trabajo de la operación (workorder).
"""

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        """Se sobrescribe la creación de órdenes de fabricación para generar quality.checks personalizados."""
        records = super().create(vals_list)
        for production in records:
            production._generate_quality_checks_by_product_center_category()
        return records

    def _generate_quality_checks_by_product_center_category(self):
        """
        Genera quality.checks durante la creación de una orden de fabricación, evaluando:

        - Si el quality.point tiene product_id, se aplica solo si coincide con el producto fabricado.
        - Si tiene product_category_ids, se aplica si el producto pertenece a esa categoría.
        - Si no tiene ni producto ni categoría, se aplica a todos los productos.

        En todos los casos, el punto solo se aplica si el workcenter_id coincide
        con el centro de trabajo de la operación correspondiente (workorder).
        """
        self.ensure_one()
        QualityCheck = self.env['quality.check']
        Product = self.product_id
        Category = Product.categ_id

        points = self.env['quality.point'].search([
            ('workcenter_id', '!=', False),
            ('operation_id', '=', False)
        ])

        for workorder in self.workorder_ids:
            for point in points:
                # Validar centro de trabajo obligatorio
                if point.workcenter_id != workorder.workcenter_id:
                    continue

                # Caso 1: punto de control asignado a un producto específico
                if point.product_id and point.product_id != Product:
                    continue

                # Caso 2: punto de control por categoría
                if point.product_category_ids and Category not in point.product_category_ids:
                    continue

                # Caso 3: punto general (sin producto ni categoría) → se permite

                # Crear el quality.check vinculado al workorder correspondiente
                QualityCheck.create({
                    'workorder_id': workorder.id,
                    'production_id': self.id,
                    'point_id': point.id,
                    'team_id': point.team_id.id,
                    'company_id': self.company_id.id,
                    'product_id': Product.id,
                })
