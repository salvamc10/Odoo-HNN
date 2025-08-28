# sale_recurring_invoicing/models/sale_order.py
from odoo import models
from datetime import date, timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_and_create_recurring_invoices(self):
        """
        Método para verificar y crear facturas de órdenes de venta recurrentes.
        Este método será llamado por un cron job en lugar de una acción automatizada.
        """
        hoy = date.today()

        # Encuentra las órdenes de venta que tienen la bandera 'recurrente'
        # y un estado que permite la facturación.
        records = self.search([
            ('x_studio_recurrente', '=', True),
            ('state', '=', 'sale'),
            ('invoice_status', '!=', 'invoiced')
        ])

        for order in records:
            # Validar vigencia del contrato
            if order.start_date and order.end_date:
                if not (order.start_date <= hoy <= order.end_date):
                    continue

            metodo = order.x_studio_mtodo_de_facturacin

            if metodo == 'Día en concreto':
                # Validar que tenga fecha definida
                if not order.x_studio_fecha:
                    continue

                fecha_objetivo = order.x_studio_fecha

                # Compara solo día y mes
                if hoy.day == fecha_objetivo.day and hoy.month == fecha_objetivo.month:
                    invoice = order._create_invoices()
                    invoice.action_post()

            elif metodo == 'Último día del mes':
                manana = hoy + timedelta(days=1)
                if manana.month != hoy.month:
                    invoice = order._create_invoices()
                    invoice.action_post()