from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)

class WebsiteSaleExtended(WebsiteSale):

    @http.route(['/website_sale/get_combination_info'], type='json', auth="public", website=True)
    def get_combination_info(self, product_template_id, product_id, combination, only_template=False, **kwargs):
        result = WebsiteSale.get_combination_info(
            self, product_template_id, product_id, combination, only_template, **kwargs
        )

        try:
            if product_id:
                product = request.env['product.product'].sudo().browse(int(product_id))
                result['x_studio_descripcion_1'] = product.x_studio_descripcion_1 or ''
        except Exception as e:
            _logger.error("Error adding custom description to variant response: %s", str(e))

        return result
