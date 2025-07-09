from odoo import models, fields, api # type: ignore

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
                rec.x_machine_number = self.env['ir.sequence'].next_by_code('custom.machine.number')
