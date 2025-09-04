from odoo import fields, models
from odoo.http import request

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    allowed_public_categ_ids = fields.Many2many(
        'product.public.category',
        'payment_provider_public_categ_rel',
        'provider_id', 'categ_id',
        string='Categorías web permitidas',
        help='Vacío: disponible para todas las categorías web. '
            'Si se seleccionan, el proveedor solo aparece cuando todas las líneas del pedido '
            'pertenecen a alguna de esas categorías o sus descendientes.'
    )

    def _get_compatible_providers(self, *args, **kwargs):
        providers = super()._get_compatible_providers(*args, **kwargs)
        try:
            ws = getattr(request, 'website', None)
            if not ws:
                return providers
            so = ws.sale_get_order()
            if not so or not so.order_line:
                return providers

            # Solo líneas contables para decidir compatibilidad
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

            countable = so.order_line.filtered(_is_countable)
            if not countable:
                return providers

            # Homogeneidad real
            groups = {so._line_group_key(l) for l in countable}
            if len(groups) != 1:
                return providers

            def order_allowed_for_provider(pv):
                if not pv.allowed_public_categ_ids:
                    return True
                allowed = pv.env['product.public.category'].search([
                    ('id', 'child_of', pv.allowed_public_categ_ids.ids)
                ]).ids
                if not allowed:
                    return False
                for l in countable:
                    if not set(l.product_id.public_categ_ids.ids).intersection(allowed):
                        return False
                return True

            return providers.filtered(order_allowed_for_provider)
        except Exception:
            return providers
