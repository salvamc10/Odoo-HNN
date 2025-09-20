from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_machine_number = fields.Char(string="Número de máquina", copy=False)

    def write(self, vals):
        result = super().write(vals)

        for mo in self:
            produced_lots = mo.lot_producing_ids
            
            # Procesar lotes producidos
            if produced_lots:
                raw_lots = mo.move_raw_ids.mapped('move_line_ids.lot_id')
                lote_origen = raw_lots.filtered(lambda l: l.x_machine_number)
                
                if lote_origen:
                    for produced_lot in produced_lots:
                        if not produced_lot.x_machine_number:
                            produced_lot.x_machine_number = lote_origen[0].x_machine_number

        return result
