# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo import _
class RepairOrder(models.Model):
    _inherit = 'repair.order'
    
    consulta_ids = fields.One2many('repair.consulta', 'repair_order_id', string="Consultas")
    type = fields.Selection(
            string="Tipo",
            selection=[('Reparación', 'Reparación'), ('Recambios', 'Recambios')],
            ondelete={'Reparación': 'cascade', 'Recambios': 'cascade'}
        )

    @api.onchange('consulta_ids')
    def _onchange_consulta_ids(self):
        """Guarda el formulario cuando se modifican las consultas."""
        if self._origin and self.consulta_ids:
            # Actualiza las consultas existentes en la base de datos
            self.write({'consulta_ids': [(1, consulta.id, {
                'consulta_text': consulta.consulta_text,
                'refer': consulta.refer,
                'product_uom_qty': consulta.product_uom_qty,
                'picked': consulta.picked,
                'product_id': consulta.product_id.id if consulta.product_id else False,
            }) for consulta in self.consulta_ids if consulta._origin]})

    def action_create_sale_order(self):
        """Override to add stock.move products to sale.order.option for type 'Recambios'."""
        # Check if any repair order is already linked to a sale order
        if any(repair.sale_order_id for repair in self):
            concerned_ro = self.filtered('sale_order_id')
            ref_str = "\n".join(ro.name for ro in concerned_ro)
            raise UserError(
                _(
                    "You cannot create a quotation for a repair order that is already linked to an existing sale order.\nConcerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                ),
            )
        # Check if partner_id is set
        if any(not repair.partner_id for repair in self):
            concerned_ro = self.filtered(lambda ro: not ro.partner_id)
            ref_str = "\n".join(ro.name for ro in concerned_ro)
            raise UserError(
                _(
                    "You need to define a customer for a repair order in order to create an associated quotation.\nConcerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                ),
            )
        
        sale_order_values_list = []
        for repair in self:
            sale_order_values_list.append({
                "company_id": repair.company_id.id,
                "partner_id": repair.partner_id.id,
                "warehouse_id": repair.picking_type_id.warehouse_id.id,
                "repair_order_ids": [(6, 0, [repair.id])],
            })
        
        # Create sale orders
        sale_orders = self.env['sale.order'].create(sale_order_values_list)
        
        # Handle stock.move products based on type
        for repair in self:
            if repair.type == 'Recambios':
                # For 'Recambios', add stock.move products to sale.order.option
                stock_moves = self.env['stock.move'].search([
                    ('repair_id', '=', repair.id),
                    ('state', '!=', 'cancel')
                ])
                sale_order = sale_orders.filtered(lambda so: repair.id in so.repair_order_ids.ids)
                if sale_order:
                    for move in stock_moves:
                        self.env['sale.order.option'].create({
                            'order_id': sale_order.id,
                            'product_id': move.product_id.id,
                            'name': move.product_id.name,
                            'quantity': move.product_uom_qty,
                            'uom_id': move.product_uom.id,
                            'price_unit': move.product_id.lst_price,
                        })
            else:
                # For other types, use the default behavior to add to sale.order.line
                repair.move_ids._create_repair_sale_order_line()
        
        return self.action_view_sale_order()
