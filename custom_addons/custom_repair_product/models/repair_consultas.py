# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class RepairConsulta(models.Model):
    _name = 'repair.consulta'
    _description = 'Consulta técnica'
    
    repair_order_id = fields.Many2one('repair.order', string="Orden de reparación")
    consulta_text = fields.Text(string="Producto a consultar")
    product_uom_qty = fields.Float(string="Cantidad")
    product_uom = fields.Many2one('uom.uom', string="Unidad de medida")
    picked = fields.Boolean(string="Usado")
