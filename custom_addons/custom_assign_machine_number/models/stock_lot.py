from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.lot'

    x_machine_number = fields.Char(string="Número de máquina", copy=False, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        lots = super().create(vals_list)

        for lot in lots:
            if not lot.x_machine_number:
                lot._try_inherit_machine_number_from_mo()

        return lots

    def _try_inherit_machine_number_from_mo(self):
        """
        Si el lote se está creando como resultado de una fabricación,
        intenta heredar el número de máquina desde los lotes consumidos.
        """
        self.ensure_one()

        # Buscar producción que produzca este lote
        production = self.env['mrp.production'].search([
            ('lot_producing_id', '=', self.id)
        ], limit=1)

        if not production:
            return

        # Buscar lotes consumidos
        raw_lots = production.move_raw_ids.mapped('move_line_ids.lot_id')
        machine_lot = raw_lots.filtered(lambda l: l.x_machine_number)

        if machine_lot:
            self.x_machine_number = machine_lot[0].x_machine_number
