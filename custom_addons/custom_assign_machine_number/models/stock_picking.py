from odoo import models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
            if picking.picking_type_id.code != 'incoming':
                continue

            for move_line in picking.move_line_ids:
                lot = move_line.lot_id
                product = move_line.product_id

                if lot and not lot.x_machine_number and product.tracking == 'serial':
                    lot.x_machine_number = self.env['ir.sequence'].next_by_code('custom.machine.number')

        return res
