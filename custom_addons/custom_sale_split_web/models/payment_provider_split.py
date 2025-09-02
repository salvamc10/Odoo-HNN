from odoo import fields, models
from odoo.http import request

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    allow_for_maquinas = fields.Boolean(string='Permitir en Máquinas', default=True)
    allow_for_recambios = fields.Boolean(string='Permitir en Recambios', default=True)

    def _get_compatible_providers(self, *args, **kwargs):
        providers = super()._get_compatible_providers(*args, **kwargs)

        # En carrito: no filtrar hasta que el pedido esté dividido y homogéneo
        try:
            ws = getattr(request, 'website', None)
            if not ws:
                return providers
            so = ws.sale_get_order()
            if not so or not so.split_done or not so.order_line:
                return providers

            group = so._line_group_key(so.order_line[0])  # 'maquinas' | 'recambios':contentReference[oaicite:2]{index=2}
            field = 'allow_for_maquinas' if group == 'maquinas' else 'allow_for_recambios'
            return providers.filtered(field)
        except Exception:
            return providers