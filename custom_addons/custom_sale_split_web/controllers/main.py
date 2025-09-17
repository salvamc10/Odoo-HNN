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

    def _siblings(self, so):
        if not so or not so.split_group_uid:
            return so.browse()
        return request.env['sale.order'].sudo().search([
            ('split_group_uid', '=', so.split_group_uid),
            ('website_id', '=', so.website_id.id),
            ('partner_id', '=', so.partner_id.id),
            ('id', '!=', so.id),
        ])

    def _has_active_tx(self, so):
        txs = getattr(so, 'transaction_ids', request.env['payment.transaction'])
        return bool(txs.filtered(lambda t: t.state in PAIDISH_STATES))

    def _group_keys(self, so):
        lines = so.order_line.filtered(self._is_countable)
        if not lines:
            return set()
        try:
            return {so._line_group_key(l) for l in lines}
        except Exception:
            return {'__single__'}  # fallback

    def _split_group_is_valid(self, so):
        """Grupo válido = exactamente 2 pedidos draft/sent, con líneas, y 1 grupo por SO."""
        bros = self._siblings(so)
        group = bros | so
        if len(group) != 2:
            return False
        for s in group:
            if s.state not in ('draft', 'sent'):
                return False
            if not s.order_line.filtered(self._is_countable):
                return False
            if len(self._group_keys(s)) != 1:
                return False
        return True

    def _purge_invalid_split(self, so):
        """Si el split no es válido, quita split_group_uid de TODOS los draft/sent del grupo."""
        if not so or not so.split_group_uid:
            return
        bros = self._siblings(so)
        group = (bros | so)
        if not group:
            return
        if self._split_group_is_valid(so):
            return
        for s in group:
            if s.state in ('draft', 'sent'):
                s.sudo().write({'split_group_uid': False})

    def _unsplit_back_to_cart(self, order):
        """
        Fusiona de vuelta si no hay pagos y ambos están en draft/sent.
        Si solo queda 1 pedido o alguno no tiene líneas, limpia split_group_uid.
        """
        if not order or not order.split_group_uid:
            return order

        so_main = order.sudo()
        bros = self._siblings(so_main)
        group = (bros | so_main)

        for s in group:
            if s.state not in ('draft', 'sent') or self._has_active_tx(s):
                return order

        alive = group.filtered(lambda s: bool(s.order_line))
        if len(alive) <= 1:
            target = alive[:1] or so_main
            target.sudo().write({'split_group_uid': False})
            request.session['sale_order_id'] = target.id
            for s in (group - target):
                if not s.order_line:
                    s.sudo().unlink()
            return target

        if any(not s.order_line.filtered(self._is_countable) for s in group):
            for s in group:
                s.sudo().write({'split_group_uid': False})
            request.session['sale_order_id'] = so_main.id
            return so_main

        return order

    @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    def cart(self, **post):
        order = request.website.sale_get_order()
        if order:
            self._purge_invalid_split(order)
            self._unsplit_back_to_cart(order)
        return WebsiteSale.cart(self, **post)

    def _get_shop_payment_values(self, order, **kwargs):
        # si el split quedó colgado, limpiar antes de nada
        if order and order.split_group_uid and not self._split_group_is_valid(order):
            self._purge_invalid_split(order)

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

        banner = False
        if order and order.split_group_uid and self._split_group_is_valid(order):
            siblings = request.env['sale.order'].sudo().search([
                ('split_group_uid', '=', order.split_group_uid),
                ('id', '!=', order.id),
                ('website_id', '=', order.website_id.id),
                ('partner_id', '=', order.partner_id.id),
            ])

            def is_recambios(so):
                lines = so.order_line.filtered(self._is_countable)
                return bool(lines) and so._line_group_key(lines[0]) == 'recambios'

            def is_paidish(so):
                if so.state in ('sale', 'done'):
                    return True
                txs = getattr(so, 'transaction_ids', request.env['payment.transaction'])
                return bool(txs.filtered(lambda t: t.state in PAIDISH_STATES))

            any_paidish = any(is_paidish(s) for s in siblings)

            if any_paidish:
                ref = next((s for s in siblings if is_paidish(s)), siblings[0])
                banner = {
                    'step_idx': 2, 'total': 2, 'mode': 'second',
                    'curr_is_recambios': is_recambios(order),
                    'other_is_recambios': is_recambios(ref),
                }
            else:
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
