from odoo import models, fields

class RepairConsulta(models.Model):
    _name = 'repair.consulta'
    _description = 'Consulta técnica'

    repair_order_id = fields.Many2one(
        'repair.order',
        string="Orden de reparación",
        ondelete='cascade'
    )
    consulta_text = fields.Text(string="Producto a consultar")
    product_uom_qty = fields.Float(string="Cantidad")
    product_uom = fields.Many2one('uom.uom', string="Unidad de medida")
    picked = fields.Boolean(string="Usado")
