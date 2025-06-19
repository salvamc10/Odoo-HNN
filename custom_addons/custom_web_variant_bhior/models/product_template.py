from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, **kwargs):
        res = super()._get_combination_info(combination=combination, **kwargs)

        # Añadir aquí el campo que quieras del product.product
        product = self.env['product.product'].browse(res.get('product_id'))
        res.update({
            'Descripcion': product.x_studio_descripcion_1 or '',  # o cualquier otro campo
        })

        return res
