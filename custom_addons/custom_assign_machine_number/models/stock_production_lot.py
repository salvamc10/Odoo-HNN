# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.lot'

    x_machine_number = fields.Char(string="Número de máquina", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._assign_machine_number()
        return records

    def write(self, vals):
        updating_machine_number = 'x_machine_number' in vals
        result = super().write(vals)
        if not updating_machine_number:
            self._assign_machine_number()
        return result

    def _assign_machine_number(self):
        """Asigna un número de máquina solo si el producto pertenece a ciertas categorías."""
        categorias_validas = {
            'Aspiradoras',
            'Barredoras',
            'Calentador Industrial',
            'Fregadoras',
            'Hidrolimpiadoras',
            'Hidrolimpiadoras / Agua Caliente',
            'Hidrolimpiadoras / Agua Fría',
            'Nebulizador',
            'Rotativa',
            'Vapor',
        }

        for rec in self:
            if rec.x_machine_number:
                continue

            categoria = rec.product_id.categ_id.name if rec.product_id and rec.product_id.categ_id else ""
            if categoria.strip() in categorias_validas:
                secuencia = self.env['ir.sequence'].sudo().next_by_code('machine.sequence')
                if secuencia:
                    rec.write({'x_machine_number': secuencia})
