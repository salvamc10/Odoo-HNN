from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo import http
from odoo.http import request

class WebsiteSaleSplit(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        if order and order.website_id and order.website_id.split_by_web_category and order.order_line:
            # Solo considerar líneas de producto reales
            def _is_countable(line):
                if getattr(line, 'display_type', False):
                    return False
                if not line.product_id:
                    return False
                if getattr(line, 'is_delivery', False):
                    return False
                if getattr(line, 'is_downpayment', False):
                    return False
                if getattr(line, 'is_reward', False):
                    return False
                return True

            countable = order.order_line.filtered(_is_countable)
            if countable:
                result = order.split_web_cart_by_category()
                countable_now = order.order_line.filtered(_is_countable)
                if not countable_now and isinstance(result, dict):
                    other = next((o for o in result.values()
                                  if o.id != order.id and o.order_line.filtered(_is_countable)), False)
                    if other:
                        request.session['sale_order_id'] = other.id
                        order = other
        return super()._get_shop_payment_values(order, **kwargs)

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        # Tras confirmar el primer pedido, si existe un hermano del mismo grupo de split en borrador,
        # redirige automáticamente a su pantalla de pago.
        last_id = request.session.get('sale_last_order_id')
        if last_id:
            so = request.env['sale.order'].sudo().browse(int(last_id))
            if so and so.exists() and so.split_group_uid:
                sibling = request.env['sale.order'].sudo().search([
                    ('id', '!=', so.id),
                    ('website_id', '=', so.website_id.id),
                    ('partner_id', '=', so.partner_id.id),
                    ('split_group_uid', '=', so.split_group_uid),
                    ('state', 'in', ['draft', 'sent']),
                ], limit=1)
                if sibling:
                    request.session['sale_order_id'] = sibling.id
                    return request.redirect('/shop/payment')
        return super().shop_payment_confirmation(**post)


class PaymentSplitRedirect(PaymentPortal):

    @http.route(['/payment/status'], type='http', auth='public', website=True, sitemap=False)
    def payment_status(self, **post):
        tx = request.env['payment.transaction'].sudo().search(
            [('id', '=', request.session.get('sale_last_tx_id'))], limit=1
        )
        if tx and tx.sale_order_ids:
            order = tx.sale_order_ids[0]
            if order.split_group_uid:
                other = request.env['sale.order'].sudo().search([
                    ('id', '!=', order.id),
                    ('state', 'in', ['draft', 'sent']),
                    ('website_id', '=', request.website.id),
                    ('partner_id', '=', order.partner_id.id),
                    ('split_group_uid', '=', order.split_group_uid),
                ], limit=1)
                if other:
                    request.session['sale_order_id'] = other.id
                    return request.redirect('/shop/payment')
        return super().payment_status(**post)
