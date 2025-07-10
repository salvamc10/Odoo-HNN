from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_machine_number = fields.Char(string="Número de máquina", copy=False)

    def write(self, vals):
        result = super().write(vals)

        for mo in self:
            if 'lot_producing_id' in vals and mo.lot_producing_id and not mo.lot_producing_id.x_machine_number:
                # Buscar lote WIP consumido con número de máquina
                raw_lots = mo.move_raw_ids.mapped('move_line_ids.lot_id')
                lote_origen = raw_lots.filtered(lambda l: l.x_machine_number)
                if lote_origen:
                    mo.lot_producing_id.x_machine_number = lote_origen[0].x_machine_number

        return result
