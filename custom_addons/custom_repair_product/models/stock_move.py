# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")
    consulta_text = fields.Char(string='Consulta')
    x_machine_number = fields.Char(related='lot_id.x_machine_number', string="Número de Máquina/Lote", store=True)