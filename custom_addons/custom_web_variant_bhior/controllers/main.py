from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class WebsiteSaleController(http.Controller):
    
    @http.route('/shop/get_product_description', type='json', auth='public', website=True, csrf=False)
    def get_product_description(self, product_id, **kwargs):
        """
        Obtener descripción personalizada del producto
        """
        try:
            product = request.env['product.product'].browse(int(product_id))
            description = getattr(product, 'x_studio_descripcion_1', '') or ''
            
            _logger.info(f"Product ID: {product_id}, Description: {description}")
            
            return {
                'description': description,
                'product_id': product.id,
                'product_name': product.name
            }
        except Exception as e:
            _logger.error(f"Error getting product description: {str(e)}")
            return {'error': str(e)}
    
    @http.route('/shop/find_product_by_attributes', type='json', auth='public', website=True, csrf=False)
    def find_product_by_attributes(self, **kwargs):
        """
        Buscar producto por template y atributos
        """
        try:
            ProductProduct = request.env['product.product']
            template_id = kwargs.get('template_id')
            attribute_ids = kwargs.get('attribute_ids', [])

            # Buscar el producto que coincida con el template y los atributos
            domain = [
                ('product_tmpl_id', '=', int(template_id))
            ]
            
            # Si hay atributos específicos, filtrar por ellos
            if attribute_ids:
                domain.append(('product_template_attribute_value_ids', 'in', attribute_ids))
            
            product = ProductProduct.search(domain, limit=1)
            
            if product:
                return {
                    'product_id': product.id,
                    'product_name': product.name
                }
            else:
                return {'error': 'Product not found'}
                
        except Exception as e:
            _logger.error(f"Error finding product by attributes: {str(e)}")
            return {'error': str(e)}