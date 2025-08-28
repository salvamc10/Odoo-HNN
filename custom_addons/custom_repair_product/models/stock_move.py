<<<<<<< HEAD
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
=======
from odoo import fields, models, api
>>>>>>> fa564c68c58d72b7d90427d683e9d227c505a725

class StockMove(models.Model):
    _inherit = 'stock.move'

<<<<<<< HEAD
    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")

=======
    lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number", 
                           domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")
    partner_repair_id = fields.Many2one(related='repair_id.partner_id', string="Cliente", store=True)
    consulta_text = fields.Char(string='Consulta')
    x_machine_number = fields.Char(related='lot_id.x_machine_number', 
                                  string="Número de Máquina/Lote", store=True)
    internal_reference = fields.Char(related='lot_id.ref', string="Referencia Interna", store=True)    
    
    @api.depends('product_id')
    def _compute_provider_id(self):
        for record in self:
            if record.product_id and record.product_id.seller_ids:
                # Tomar el primer proveedor disponible
                record.provider_id = record.product_id.seller_ids[0].id
            else:
                record.provider_id = False

    provider_id = fields.Many2one('product.supplierinfo', string="Proveedor", 
                                compute='_compute_provider_id', store=True)
    provider_reference = fields.Char(related='provider_id.product_code', 
                                   string="Referencia Proveedor", store=True)
    provider_ids = fields.One2many(related='product_id.seller_ids', string="Proveedores", readonly=True)
    # description = fields.Html(related='lot_id.note', string="Descripción", store=True)
    
    estado_recambio = fields.Selection(
        string="Estado Recambio",
        selection=[
            ('Pte almacenar', 'Pte de almacenar'), 
            ('Estanteria', 'Estanteria'),
            ('Stock', 'Stock'),
            ('Montado/servido', 'Montado/servido')
        ],
        compute='_onchange_estado_recambio',
        store=True
    )

    @api.onchange('location_id', 'picked')
    def _onchange_estado_recambio(self):
        """
        Actualiza el estado del recambio basado en la ubicación de destino y si está marcado como picked.
        Este método se ejecuta en el cliente cuando cambian los campos, útil para formularios.
        """
        for record in self:
            estado = False
            location = record.location_id
            if not location:
                record.estado_recambio = estado
                continue

            # 1. Montado/servido: Si picked está marcado O la ubicación es Customer
            if record.picked or location.usage == 'customer':
                estado = 'Montado/servido'

            # 2. Pte almacenar: Si la ubicación es Input (WH/Input)
            elif location.usage == 'input':
                estado = 'Pte almacenar'

            # 3. Stock: Si la ubicación es la ubicación principal de Stock (WH/Stock)
            elif location.usage == 'internal' and location.name.lower() == 'stock':
                estado = 'Stock'

            # 4. Estanteria: Cualquier otra ubicación interna que no sea Stock principal
            elif location.usage == 'internal':
                estado = 'Estanteria'

            record.estado_recambio = estado

    # @api.onchange('estado_recambio')
    # def _onchange_estado_recambio(self):
    #     """
    #     Marca como picked cuando el estado es Montado/servido
    #     """
    #     if self.estado_recambio == 'Montado/servido':
    #         self.picked = True
    
    # @api.model
    # def _recalculate_all_estados(self):
    #     """
    #     Método para recalcular todos los estados - ejecutar una vez después de la actualización
    #     """
    #     all_moves = self.search([('state', '=', 'done')])
    #     all_moves._compute_estado_recambio()
    #     return len(all_moves)
>>>>>>> fa564c68c58d72b7d90427d683e9d227c505a725
