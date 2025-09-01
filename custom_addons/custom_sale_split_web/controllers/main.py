from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request

class WebsiteSaleSplit(WebsiteSale):
    """
    Controlador web para:
      - Redirigir a una pantalla intermedia de "Resumen de división" tras el split.
      - Alternar el carrito activo para pagar cada pedido resultante del split.
    """

    # --------- Paso intermedio: resumen de la división ---------
    @http.route(['/shop/split-summary'], type='http', auth='public', website=True)
    def split_summary(self, **kw):
        website = request.website
        order = website.sale_get_order()
        if not order or not order.split_done:
            return request.redirect('/shop/cart')

        # Intentar recuperar los pedidos separados desde sesión
        so_ids = set()
        sess = request.session.get('split_orders') or {}
        for so_id in sess.values():
            if so_id:
                so_ids.add(so_id)

        # Fallback: asegurar que al menos aparece el pedido actual
        so_ids.add(order.id)

        orders = request.env['sale.order'].sudo().browse(list(so_ids))
        return request.render('custom_split.split_summary', {
            'orders': orders,
            'current_order_id': order.id,
        })

    # --------- Hook de pago: dispara split y redirige al resumen ---------
    def _get_shop_payment_values(self, order, **kwargs):
        # Si procede, dividir el carrito antes de continuar
        if order and order.website_id \
           and order.website_id.split_by_web_category \
           and not order.split_done:
            orders = order.split_web_cart_by_category()  # {'maquinas': so?, 'recambios': so?}

            # Guardar en sesión los IDs para mostrarlos en el resumen
            request.session['split_orders'] = {k: v.id for k, v in orders.items() if v}
            return request.redirect('/shop/split-summary')

        # Si ya estaba dividido, forzar visualización del resumen
        if order and order.split_done:
            return request.redirect('/shop/split-summary')

        # Comportamiento estándar si no hay split
        return super()._get_shop_payment_values(order, **kwargs)

    # --------- Alternar el pedido activo y llevar a pago ---------
    @http.route(['/shop/switch_order/<int:so_id>'], type='http', auth='public', website=True)
    def switch_order(self, so_id, **kw):
        website = request.website
        so = request.env['sale.order'].sudo().browse(so_id)

        # Partner del usuario (público u autenticado)
        user_partner = (
            website.user_id.partner_id
            if request.env.user._is_public()
            else request.env.user.partner_id
        )

        # Validaciones mínimas de seguridad y consistencia
        if not so or not so.exists():
            return request.redirect('/shop/cart')
        if so.website_id.id != website.id:
            return request.redirect('/shop/cart')
        if so.partner_id.commercial_partner_id.id != user_partner.commercial_partner_id.id:
            return request.redirect('/shop/cart')

        # Cambiar el pedido activo en sesión y llevar a pago
        request.session['sale_order_id'] = so.id
        return request.redirect('/shop/payment')
