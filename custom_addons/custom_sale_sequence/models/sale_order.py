# -*- coding: utf-8 -*-
"""
Módulo: custom_sale_sequence

Este módulo personaliza la numeración de pedidos de venta en función de la plantilla seleccionada.
Cuando el pedido se encuentra en estado 'draft', 'sent' o 'cancel', y su nombre empieza por 'S',
se le asigna una nueva secuencia personalizada según la plantilla de presupuesto utilizada.

Reemplaza automatizaciones previas realizadas con Odoo Studio.

Autor: Salva M - Web Rental Solutions
Fecha: abril 2025
"""

from odoo import models, api # type: ignore


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._apply_custom_sequence()
        return records

    def write(self, vals):
        """
        Aplica la lógica de secuencia personalizada también al modificar un pedido.
        Es compatible con escrituras en lote (recordsets múltiples).
        """
        result = super().write(vals)
        for record in self:
            record._apply_custom_sequence()
        return result

    def _apply_custom_sequence(self):
        """
        Aplica una secuencia personalizada al pedido de venta según su plantilla.

        Condiciones:
            - El pedido debe estar en estado 'draft', 'sent' o 'cancel'.
            - El nombre del pedido debe comenzar por 'S'.
            - Debe haber una plantilla de presupuesto válida vinculada.
            - La plantilla debe estar mapeada a una secuencia definida en ir.sequence.

        Efecto:
            - El campo `origin` toma el valor actual del nombre.
            - El campo `name` se reemplaza por la nueva secuencia.
        """
        for record in self:
            if record.state in ['draft', 'sent', 'cancel'] and record.name.startswith('S'):
                sequence_mapping = {
                    'Alquiler': 'sequence_alquiler',
                    'Maquina': 'sequence_maquina',
                    'Recambio': 'sequence_recambio',
                    'Reparacion': 'sequence_reparacion',
                }

                template_name = record.sale_order_template_id.name if record.sale_order_template_id else False
                sequence_id = sequence_mapping.get(template_name)

                if sequence_id:
                    sequence = self.env['ir.sequence'].sudo().next_by_code(sequence_id)
                    if sequence:
                        record.write({
                            'origin': record.name,
                            'name': sequence,
                        })
