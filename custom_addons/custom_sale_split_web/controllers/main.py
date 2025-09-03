from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo import http
from odoo.http import request

PAIDISH_STATES = ('pending', 'authorized', 'done', 'posted')

class WebsiteSaleSplit(WebsiteSale):
    def _is_countable(self, line):
        return (
            not getattr(line, 'display_type', False)
            and bool(line.product_id)
            and not getattr(line, 'is_delivery', False)
            and not getattr(line, 'is_downpayment', False)
            and not getattr(line, 'is_reward', False)
        )

    def _get_shop_payment_values(self, order, **kwargs):
        # asegurar split activo y mover al hijo si toca
        if order and order.website_id and order.website_id.split_by_web_category and order.order_line:
            countable = order.order_line.filtered(self._is_countable)
            if countable:
                result = order.split_web_cart_by_category()
                countable_now = order.order_line.filtered(self._is_countable)
                if not countable_now and isinstance(result, dict):
                    other = next((o for o in result.values()
                                  if o.id != order.id and o.order_line.filtered(self._is_countable)), False)
                    if other:
                        request.session['sale_order_id'] = other.id
                        order = other

        values = super()._get_shop_payment_values(order, **kwargs)

        # --- Banner robusto ---
        banner = False
        if order and order.split_group_uid:
            siblings = request.env['sale.order'].sudo().search([
                ('split_group_uid', '=', order.split_group_uid),
                ('id', '!=', order.id),
                ('website_id', '=', order.website_id.id),
                ('partner_id', '=', order.partner_id.id),
            ])
            if siblings:
                def is_recambios(so):
                    lines = so.order_line.filtered(self._is_countable)
                    return bool(lines) and so._line_group_key(lines[0]) == 'recambios'

                # ¿Algún hermano ya está cobrado/confirmado o con transacción en curso?
                def is_paidish(so):
                    if so.state in ('sale', 'done'):
                        return True
                    txs = getattr(so, 'transaction_ids', request.env['payment.transaction'])
                    return bool(txs.filtered(lambda t: t.state in PAIDISH_STATES))

                any_paidish = any(is_paidish(s) for s in siblings)

                if any_paidish:
                    # Estamos en el segundo paso
                    ref = next((s for s in siblings if is_paidish(s)), siblings[0])
                    banner = {
                        'step_idx': 2, 'total': 2, 'mode': 'second',
                        'curr_is_recambios': is_recambios(order),
                        'other_is_recambios': is_recambios(ref),
                    }
                else:
                    # Nadie pagado aún -> primer paso
                    ref = siblings[0]
                    banner = {
                        'step_idx': 1, 'total': 2, 'mode': 'first',
                        'curr_is_recambios': is_recambios(order),
                        'other_is_recambios': is_recambios(ref),
                    }

        values['split_banner'] = banner
        return values

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
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
                    # sincronizar transportista si falta
                    if getattr(so, 'carrier_id', False) and not getattr(sibling, 'carrier_id', False):
                        sibling.write({'carrier_id': so.carrier_id.id})
                        if hasattr(sibling, '_update_delivery_price'):
                            try:
                                sibling._update_delivery_price()
                            except Exception:
                                pass
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
                    if getattr(order, 'carrier_id', False) and not getattr(other, 'carrier_id', False):
                        other.write({'carrier_id': order.carrier_id.id})
                        if hasattr(other, '_update_delivery_price'):
                            try:
                                other._update_delivery_price()
                            except Exception:
                                pass
                    request.session['sale_order_id'] = other.id
                    return request.redirect('/shop/payment')
        return super().payment_status(**post)
