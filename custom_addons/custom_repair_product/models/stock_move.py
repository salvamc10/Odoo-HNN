from odoo import fields, models, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number", domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")
    partner_repair_id = fields.Many2one(related='repair_id.partner_id', string="Cliente", store=True)
    consulta_text = fields.Char(string='Consulta')
    x_machine_number = fields.Char(related='lot_id.x_machine_number', string="Número de Máquina/Lote", store=True)
    internal_reference = fields.Char(related='lot_id.ref', string="Referencia Interna", store=True)    
    provider_reference = fields.Char(related='provider_id.product_code', string="Referencia Proveedor", store=True)
    provider_id = fields.Many2one('product.supplierinfo', string="Proveedor", store=True)
    description = fields.Html(related='lot_id.note', string="Descripción", store=True)
    estado_recambio = fields.Selection(
            string="Estado Recambio",
            selection=[('Pte almacenar', 'Pte de almacenar'), 
                       ('Estanteria', 'Estanteria'),
                       ('Stock', 'Stock'),
                       ('Montado/servido', 'Montado/servido')],
            ondelete={'Pte almacenar': 'cascade', 'Estanteria': 'cascade', 'Stock': 'cascade', 'Montado/servido': 'cascade'},
            compute='_compute_estado_recambio',
            store=True,
            readonly=False
        )

    @api.depends('location_dest_id', 'location_id', 'state', 'picked', 'purchase_line_id')
    def _compute_estado_recambio(self):
        """
        Computa el estado del recambio basado en su ubicación y contexto
        """
        for record in self:
            estado = False
            
            # 1. Montado/servido: Si está marcado como picked o se ha usado
            if record.picked or record._is_component_used():
                estado = 'Montado/servido'
            
            # 2. Pte almacenar: Recepción en 2 pasos, primera recepción desde compra
            elif record._is_pending_storage():
                estado = 'Pte almacenar'
            
            # 3. Estanteria: Ubicado en sub-ubicación de Stock (ej: WH/Stock/shelf1)
            elif record._is_in_shelf_location():
                estado = 'Estanteria'
            
            # 4. Stock: Ubicado en la ubicación padre Stock (ej: WH/Stock)
            elif record._is_in_stock_location():
                estado = 'Stock'
            
            record.estado_recambio = estado

    def _is_pending_storage(self):
        """
        Verifica si el movimiento está pendiente de almacenamiento
        Aplica cuando:
        - Viene de una compra
        - Almacén configurado para recepción en 2 pasos
        - Es la primera recepción (location_dest_id es input location)
        """
        if not self.purchase_line_id:
            return False
            
        # Obtener el almacén de destino
        warehouse = self.location_dest_id.warehouse_id
        if not warehouse:
            return False
            
        # Verificar si está configurado para recepción en 2 pasos
        if warehouse.reception_steps != 'two_steps':
            return False
            
        # Verificar si la ubicación de destino es la ubicación de entrada/input
        return self.location_dest_id == warehouse.wh_input_stock_loc_id

    def _is_in_shelf_location(self):
        """
        Verifica si está en una sub-ubicación de Stock (estantería)
        """
        if not self.location_dest_id:
            return False
            
        # Obtener la ubicación de stock del almacén
        warehouse = self.location_dest_id.warehouse_id
        if not warehouse or not warehouse.lot_stock_id:
            return False
            
        stock_location = warehouse.lot_stock_id
        
        # Verificar si es una sub-ubicación de Stock pero no la ubicación Stock principal
        return (self.location_dest_id.location_id == stock_location and 
                self.location_dest_id != stock_location and
                self.state == 'done')

    def _is_in_stock_location(self):
        """
        Verifica si está en la ubicación padre Stock
        """
        if not self.location_dest_id:
            return False
            
        warehouse = self.location_dest_id.warehouse_id
        if not warehouse:
            return False
            
        # Verificar si está exactamente en la ubicación Stock principal
        return (self.location_dest_id == warehouse.lot_stock_id and 
                self.state == 'done')

    def _is_component_used(self):
        """
        Verifica si el componente se ha usado en una reparación o venta
        """
        # Verificar si está relacionado con una orden de reparación completada
        if self.repair_id and self.repair_id.state in ['done', 'invoice']:
            return True
            
        # Verificar si está en una orden de venta de reparación
        if (hasattr(self, 'sale_line_id') and self.sale_line_id and 
            self.sale_line_id.order_id.repair_id):
            return True
            
        # Verificar si es un movimiento de salida desde stock hacia producción/uso
        if (self.location_id.usage == 'internal' and 
            self.location_dest_id.usage in ['production', 'customer'] and
            self.state == 'done'):
            return True
            
        return False
    
    @api.onchange('estado_recambio')
    def onchange_estado_recambio(self):
        """
        Marca como picked cuando el estado es Montado/servido
        """
        for record in self:
            if record.estado_recambio == 'Montado/servido':
                record.picked = True
    
    def write(self, vals):
        """
        Override write para recalcular estado cuando cambian campos relevantes
        """
        result = super().write(vals)
        
        # Campos que pueden afectar el estado del recambio
        trigger_fields = ['location_dest_id', 'location_id', 'state', 'picked']
        
        if any(field in vals for field in trigger_fields):
            self._compute_estado_recambio()
            
        return result