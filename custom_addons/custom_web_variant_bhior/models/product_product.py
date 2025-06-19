from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_combination_info_variant(self, **kwargs):
        res = super()._get_combination_info_variant(**kwargs)
        res['x_studio_descripcion_1'] = self.x_studio_descripcion_1 or ''
        return res
