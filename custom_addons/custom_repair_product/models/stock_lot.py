from odoo import fields, models

class StockLot(models.Model):
    _inherit = 'stock.lot'

    x_machine_number = fields.Char(string="Número de Máquina/Lote")
