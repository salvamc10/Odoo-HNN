# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")
    consulta_text = fields.Char(string='Consulta')
