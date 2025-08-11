from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http

class WebsiteSaleSplit(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        if order and order.website_id and order.website_id.split_by_web_category and not order.split_done:
            order.split_web_cart_by_category()
        return super()._get_shop_payment_values(order, **kwargs)
