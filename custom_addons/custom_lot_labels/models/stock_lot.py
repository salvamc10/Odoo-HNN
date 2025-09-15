from odoo import models, fields, api

class StockLotInherit(models.Model):
    _inherit = 'stock.lot'

    # Comprobación en tiempo de carga si existe el campo
    if not hasattr(_inherit, 'x_machine_number'):
        x_machine_number = fields.Char(
            string='Número de máquina',
            help='Número de identificación de la máquina asociado al lote.'
        )
