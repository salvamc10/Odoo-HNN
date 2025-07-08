from odoo import models, fields, api # type: ignore

class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_below_minimum_qty = fields.Float(
        string='Unidades faltantes para mínimo',
        compute='_compute_stock_below_minimum_qty',
        store=True
    )

    @api.depends('qty_available')
    def _compute_stock_below_minimum_qty(self):
        Orderpoint = self.env['stock.warehouse.orderpoint']
        for product in self:
            orderpoint = Orderpoint.search([('product_id', '=', product.id)], limit=1)
            if orderpoint and orderpoint.product_min_qty > 0:
                missing = orderpoint.product_min_qty - product.qty_available
                product.stock_below_minimum_qty = missing if missing > 0 else 0.0
            else:
                product.stock_below_minimum_qty = 0.0
