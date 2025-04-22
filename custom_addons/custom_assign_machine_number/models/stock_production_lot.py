from odoo import models, api # type: ignore

class StockLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def create(self, vals):
        lot = super(StockLot, self).create(vals)
        # sólo si el campo existe en este entorno
        if 'x_studio_numero_de_maquina' in lot._fields:
            lot._assign_machine_number()
        return lot

    @api.multi
    def write(self, vals):
        res = super(StockLot, self).write(vals)
        # (opcional) volver a asignar si quieres pisar en write
        return res

    @api.multi
    def _assign_machine_number(self):
        categorias_validas = {'Nebulizador', 'Rotativa', 'Vapor'}
        for rec in self:
            # si no existe el campo en la definición, _fields lo aborta
            if not rec._fields.get('x_studio_numero_de_maquina'):
                continue
            # si ya tiene número, no tocar
            if rec.x_studio_numero_de_maquina:
                continue
            cat = (rec.product_id.categ_id.name or '').strip()
            if cat in categorias_validas:
                seq = self.env['ir.sequence'].sudo().next_by_code('machine.sequence')
                if seq:
                    rec.write({'x_studio_numero_de_maquina': seq})
