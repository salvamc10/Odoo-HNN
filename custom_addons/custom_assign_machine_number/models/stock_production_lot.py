# -*- coding: utf-8 -*-
from odoo import models, api

class StockLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def create(self, vals):
        lot = super().create(vals)
        # sólo si el campo existe, lo asignamos
        if 'x_studio_numero_de_maquina' in lot._fields:
            lot._assign_machine_number()
        return lot

    def write(self, vals):
        res = super().write(vals)
        # si quisieras también disparar algo tras write, lo harías aquí
        return res

    def _assign_machine_number(self):
        categorias_validas = {'Nebulizador', 'Rotativa', 'Vapor'}
        for rec in self:
            # si el campo no existe, saltamos
            if 'x_studio_numero_de_maquina' not in rec._fields:
                continue
            # si ya tiene número, no hacemos nada
            if rec.x_studio_numero_de_maquina:
                continue
            cat = (rec.product_id.categ_id.name or '').strip()
            if cat in categorias_validas:
                seq = self.env['ir.sequence'].sudo().next_by_code('machine.sequence')
                if seq:
                    rec.write({'x_studio_numero_de_maquina': seq})
