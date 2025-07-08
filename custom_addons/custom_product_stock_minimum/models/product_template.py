from odoo import models, fields, api # type: ignore
from datetime import datetime

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_below_minimum_qty = fields.Float(
        string='Unidades faltantes para mínimo',
        compute='_compute_stock_below_minimum_qty',
        store=True
    )

    stock_counted = fields.Boolean(
        string='Recuento Inventario'
    )

    stock_count_marked_date = fields.Datetime(
        string='Fecha de marcado recuento',
        readonly=True
    )

    @api.depends('product_variant_ids.qty_available')
    def _compute_stock_below_minimum_qty(self):
        Orderpoint = self.env['stock.warehouse.orderpoint']
        for template in self:
            qty_available = sum(template.product_variant_ids.mapped('qty_available'))
            orderpoint = Orderpoint.search([
                '|',
                ('product_id.product_tmpl_id', '=', template.id),
                ('product_tmpl_id', '=', template.id),
            ], limit=1)
            if orderpoint and orderpoint.product_min_qty > 0:
                missing = orderpoint.product_min_qty - qty_available
                template.stock_below_minimum_qty = missing if missing > 0 else 0.0
            else:
                template.stock_below_minimum_qty = 0.0

    def write(self, vals):
        if 'stock_counted' in vals and vals['stock_counted']:
            vals['stock_count_marked_date'] = datetime.now()
        return super().write(vals)
