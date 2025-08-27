from odoo import fields, models, api

class StockMove(models.Model):
    _inherit = 'stock.move'

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
    description = fields.Html(related='lot_id.note', string="Descripción", store=True)
    
    estado_recambio = fields.Selection(
        string="Estado Recambio",
        selection=[
            ('Pte almacenar', 'Pte de almacenar'), 
            ('Estanteria', 'Estanteria'),
            ('Stock', 'Stock'),
            ('Montado/servido', 'Montado/servido')
        ],
        compute='_compute_estado_recambio',
        store=True
    )

    @api.depends('location_dest_id', 'state', 'picked')
    def _compute_estado_recambio(self):
        """
        Computa el estado del recambio basado en la ubicación de destino
        """
        for record in self:
            estado = False
                
            # Si no hay ubicación de destino, no podemos determinar el estado
            if not record.location_dest_id:
                record.estado_recambio = estado
                continue

            # 1. Montado/servido: Si picked está marcado O la ubicación es Customer
            if record.picked or record.location_dest_id.usage == 'customer':
                estado = 'Montado/servido'
            
            # 2. Pte almacenar: Si la ubicación es Input (WH/Input)
            elif record.location_dest_id.usage == 'input':
                estado = 'Pte almacenar'
            
            # 3. Stock: Si la ubicación es la ubicación principal de Stock (WH/Stock)
            elif (record.location_dest_id.usage == 'internal' and 
                  record.location_dest_id.warehouse_id and
                  record.location_dest_id == record.location_dest_id.warehouse_id.lot_stock_id):
                estado = 'Stock'
            
            # 4. Estanteria: Cualquier otra ubicación interna que no sea Stock principal
            elif record.location_dest_id.usage == 'internal':
                estado = 'Estanteria'

            record.estado_recambio = estado

    @api.onchange('estado_recambio')
    def _onchange_estado_recambio(self):
        """
        Marca como picked cuando el estado es Montado/servido
        """
        if self.estado_recambio == 'Montado/servido':
            self.picked = True
    
    @api.model
    def _recalculate_all_estados(self):
        """
        Método para recalcular todos los estados - ejecutar una vez después de la actualización
        """
        all_moves = self.search([('state', '=', 'done')])
        all_moves._compute_estado_recambio()
        return len(all_moves)