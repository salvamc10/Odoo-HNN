from odoo import fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number", domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")
    consulta_text = fields.Char(string='Consulta')
    x_machine_number = fields.Char(related='lot_id.x_machine_number', string="Número de Máquina/Lote", store=True)