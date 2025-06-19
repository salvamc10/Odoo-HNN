from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_studio_descripcion_1 = fields.Html(string="Descripción Custom")

    def _get_combination_info_variant(self, **kwargs):
        res = super()._get_combination_info_variant(**kwargs)

        print(f"DEBUG: res = {res}")
        print(f"DEBUG: self = {self}")
        print(f"DEBUG: has field = {hasattr(self, 'x_studio_descripcion_1')}")
        
        # Verificar que el campo existe antes de acceder
        if hasattr(self, 'x_studio_descripcion_1'):
            res['x_studio_descripcion_1'] = self.x_studio_descripcion_1 or ''
        return res