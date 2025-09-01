from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo import http
from odoo.http import request


class WebsiteSaleSplit(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        if order and order.website_id and order.website_id.split_by_web_category and not order.split_done:
            order.split_web_cart_by_category()
        return super()._get_shop_payment_values(order, **kwargs)

    @http.route(['/shop/cart/update_json'], type='json', auth="public", website=True)
    def cart_update_json(self, product_id, add_qty=1, **kw):
        product = request.env['product.product'].browse(int(product_id))
        current_order = request.website.sale_get_order(force_create=True)
        return super().cart_update_json(product_id=product_id, add_qty=add_qty, **kw)


class PaymentSplitRedirect(PaymentPortal):

    @http.route(['/payment/status'], type='http', auth='public', website=True, sitemap=False)
    def payment_status(self, **post):
        tx = request.env['payment.transaction'].sudo().search([
            ('id', '=', request.session.get('sale_last_tx_id'))
        ], limit=1)

        if tx and tx.sale_order_ids:
            order = tx.sale_order_ids[0]
            if order.split_done:
                current_type = order._line_group_key(order.order_line[0])
                opposite_type = 'recambios' if current_type == 'maquinas' else 'maquinas'

                other = request.env['sale.order'].sudo().search([
                    ('origin', '=', order.name),
                    ('id', '!=', order.id),
                    ('split_done', '=', True),
                    ('state', '=', 'draft'),
                    ('website_id', '=', request.website.id),
                    ('partner_id', '=', order.partner_id.id),
                ], limit=1)

                if other:
                    request.session['sale_order_id'] = other.id
                    return request.redirect('/shop/payment')

        return super().payment_status(**post)
