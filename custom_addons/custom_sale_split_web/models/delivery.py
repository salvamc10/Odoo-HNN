from odoo import api, models

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def _get_price_available(self, order):
        """Extend delivery price calculation to consider split order totals"""
        # Si el pedido pertenece a un grupo dividido y tenemos el total del grupo en contexto
        if order.split_group_uid and self.env.context.get('split_group_total'):
            # Guardamos el amount_untaxed original
            original_amount = order.amount_untaxed
            total_group_amount = self.env.context.get('split_group_total')
            
            # Si el método tiene una regla basada en precio
            if self.free_over and self.amount <= total_group_amount and total_group_amount >= self.amount:
                # Si el total del grupo supera el umbral para envío gratis
                return 0.0
            
        # Continuar con el cálculo normal
        return super()._get_price_available(order)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def _get_split_group_orders(self):
        """Obtiene todos los pedidos del mismo grupo dividido"""
        self.ensure_one()
        if not self.split_group_uid:
            return self
        
        return self.search([('split_group_uid', '=', self.split_group_uid)])
    
    @api.depends('order_line.price_total')
    def _compute_amount_all(self):
        """Override para recalcular costes de envío cuando cambia el importe"""
        super()._compute_amount_all()
        
        # Si este pedido forma parte de un grupo dividido
        for order in self:
            if order.split_group_uid and order.state in ['draft', 'sent']:
                # Obtener todos los pedidos del grupo
                group_orders = order._get_split_group_orders()
                if len(group_orders) > 1 and order.carrier_id:
                    # Calcular el total del grupo
                    total_amount = sum(o.amount_untaxed for o in group_orders)
                    # Actualizar el precio del envío teniendo en cuenta el total del grupo
                    order.with_context(split_group_total=total_amount)._update_delivery_price()

    def _update_delivery_price(self):
        """Extiende el método para considerar el total del grupo en los pedidos divididos"""
        # Si el pedido forma parte de un grupo dividido y no tenemos el total en contexto
        if self.split_group_uid and not self.env.context.get('split_group_total') and self.carrier_id:
            # Obtener todos los pedidos del grupo
            group_orders = self._get_split_group_orders()
            if len(group_orders) > 1:
                # Calcular el total del grupo
                total_amount = sum(order.amount_untaxed for order in group_orders)
                # Llamar al método con el total del grupo en contexto
                return super(SaleOrder, self.with_context(split_group_total=total_amount))._update_delivery_price()
        
        # Comportamiento normal
        return super()._update_delivery_price()