# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class RepairOrder(models.Model):
    _inherit = 'repair.order'
    
    consulta_ids = fields.One2many('repair.consulta', 'repair_order_id', string="Consultas")

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
