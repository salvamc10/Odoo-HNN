from odoo import models, api, fields

class RepairProductLine(models.Model):
    _name = 'repair.product.line'
    _description = 'Línea agregada de productos de reparación'
    _auto = False  # Es un modelo de solo lectura basado en una vista SQL

    move_id = fields.Many2one('stock.move', string='Movimiento', readonly=True)
    repair_id = fields.Many2one('repair.order', string='Orden de reparación', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    product_uom_qty = fields.Float(string='Cantidad prevista', readonly=True)
    quantity = fields.Float(string='Cantidad', readonly=True)
    product_uom = fields.Many2one('uom.uom', string='UdM', readonly=True)
    picked = fields.Boolean(string='Recogido', readonly=True)
    repair_line_type = fields.Selection([
        ('add', 'Añadir'),
        ('remove', 'Quitar'),
    ], string='Tipo de línea', readonly=True)

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW repair_product_line AS (
                SELECT
                    sm.id AS id,
                    sm.id AS move_id,
                    sm.repair_id AS repair_id,
                    sm.product_id AS product_id,
                    sm.product_uom_qty AS product_uom_qty,
                    sm.quantity AS quantity,
                    sm.product_uom AS product_uom,
                    sm.picked AS picked,
                    sm.repair_line_type AS repair_line_type
                FROM stock_move sm
                WHERE sm.repair_id IS NOT NULL
            )
        """)