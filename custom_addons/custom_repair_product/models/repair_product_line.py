from odoo import models, api, fields

class RepairProductLine(models.Model):
    _name = 'repair.product.line'
    _description = 'Línea agregada de productos de reparación'
    _auto = False  # Es un modelo de solo lectura basado en una vista SQL

    repair_id = fields.Many2one('repair.order', string='Orden de reparación', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    product_uom_qty = fields.Float(string='Cantidad', readonly=True)
    location_id = fields.Many2one('stock.location', string='Ubicación', readonly=True)
    lot_id = fields.Many2one('stock.lot', string='Lote/Serie', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('ready', 'Preparado'),
        ('under_repair', 'En reparación'),
        ('done', 'Hecho'),
        ('cancel', 'Cancelado')
    ], string='Estado reparación', readonly=True)

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE VIEW repair_product_line AS (
                SELECT
                    rol.id AS id,
                    rol.repair_id AS repair_id,
                    rol.product_id AS product_id,
                    rol.product_uom_qty AS product_uom_qty,
                    ro.location_id AS location_id,
                    rol.lot_id AS lot_id,
                    ro.state AS state
                FROM repair_order_line rol
                JOIN repair_order ro ON rol.repair_id = ro.id
            )
        """)