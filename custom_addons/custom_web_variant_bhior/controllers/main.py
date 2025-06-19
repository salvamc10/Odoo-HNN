from odoo import http
from odoo.http import request

class WebsiteSaleController(http.Controller):
    
    # @http.route('/shop/product_configurator', type='json', auth='public', website=True)
    # def product_configurator(self, **kwargs):
    #     # Tu lógica aquí
    #     return request.env['product.product']._get_combination_info(**kwargs)

    @http.route('/shop/get_custom_description', type='json', auth='public', website=True)
    def get_custom_description(self, product_id, **kwargs):
        product = request.env['product.product'].browse(int(product_id))
        return {
            'description': product.x_studio_descripcion_1 or ''
        }