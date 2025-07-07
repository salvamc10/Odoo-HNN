from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_studio_descripcion_1 = fields.Html(string="Descripción Custom")

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(
        self, combination=False, product_id=False, add_qty=1.0,
        parent_combination=False, only_template=False,
    ):
        # Llamar al método original de Odoo
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        # Obtener el producto relacionado (si existe)
        product = self.env['product.product'].browse(combination_info.get('product_id'))

        # Inyectar el campo personalizado
        combination_info['x_studio_descripcion_1'] = product.x_studio_descripcion_1 or ''

        return combination_info

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'
    
    def _get_combination_name(self):
        """Exclude values from single value lines or from no_variant attributes."""
        ptavs = self._without_no_variant_attributes().with_prefetch(self._prefetch_ids)
        ptavs = ptavs._filter_single_value_lines().with_prefetch(self._prefetch_ids)
        return ", ".join([ptav.name or "" for ptav in ptavs])
