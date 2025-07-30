# -*- coding: utf-8 -*-
"""
Módulo: custom_sale_sequence

Este módulo personaliza la numeración de pedidos de venta en función de la plantilla seleccionada.
También detecta si el presupuesto proviene de una reparación para asignar automáticamente
la plantilla y secuencia correspondiente.

Autor: Salva M
Fecha: julio 2025
"""

from odoo import models, api, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        sequence_mapping = {
            'Alquiler': 'sequence_alquiler',
            'Maquina': 'sequence_maquina',
            'Recambio': 'sequence_recambio',
            'Reparacion': 'sequence_reparacion',
        }

        for vals in vals_list:
            # Si viene de reparación, asignar plantilla automáticamente
            if not vals.get('sale_order_template_id') and vals.get('origin'):
                repair = self.env['repair.order'].sudo().search([('name', '=', vals['origin'])], limit=1)
                if repair:
                    template = self.env.ref('custom_sale_template_reparacion', raise_if_not_found=False)
                    if template:
                        vals['sale_order_template_id'] = template.id

            # Asignar secuencia al crear, según plantilla
            template_id = vals.get('sale_order_template_id')
            if template_id:
                template = self.env['sale.order.template'].browse(template_id)
                sequence_code = sequence_mapping.get(template.name)
                if sequence_code:
                    vals['name'] = self.env['ir.sequence'].sudo().next_by_code(sequence_code)

        return super().create(vals_list)

    def write(self, vals):
        sequence_mapping = {
            'Alquiler': 'sequence_alquiler',
            'Maquina': 'sequence_maquina',
            'Recambio': 'sequence_recambio',
            'Reparacion': 'sequence_reparacion',
        }

        # Detectar si se ha cambiado la plantilla y si el pedido sigue siendo borrador
        if 'sale_order_template_id' in vals:
            for order in self:
                if order.state in ['draft', 'sent']:
                    new_template = self.env['sale.order.template'].browse(vals['sale_order_template_id'])
                    sequence_code = sequence_mapping.get(new_template.name)
                    if sequence_code:
                        new_seq = self.env['ir.sequence'].sudo().next_by_code(sequence_code)
                        if new_seq:
                            vals['name'] = new_seq

        return super().write(vals)
        