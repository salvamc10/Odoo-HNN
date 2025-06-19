from odoo import models, fields

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'
    
    def _get_combination_name(self):
        """Exclude values from single value lines or from no_variant attributes."""
        ptavs = self._without_no_variant_attributes().with_prefetch(self._prefetch_ids)
        ptavs = ptavs._filter_single_value_lines().with_prefetch(self._prefetch_ids)
        return ", ".join([ptav.name or "" for ptav in ptavs])
