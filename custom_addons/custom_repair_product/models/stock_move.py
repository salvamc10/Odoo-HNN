from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

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
    provider_reference = fields.Char(related='provider_id.product_code', 
                                   string="Referencia Proveedor", store=True)
    provider_ids = fields.One2many(
        related='lot_id.product_id.seller_ids',
        string="Proveedores",
        readonly=True
    )
    description = fields.Html(related='lot_id.note', string="Descripción", store=True)
    estado_recambio = fields.Selection(
        string="Estado Recambio",
        selection=[
            ('Pte almacenar', 'Pte de almacenar'), 
            ('Estanteria', 'Estanteria'),
            ('Stock', 'Stock'),
            ('Montado/servido', 'Montado/servido')
        ],
        ondelete={
            'Pte almacenar': 'cascade', 
            'Estanteria': 'cascade', 
            'Stock': 'cascade', 
            'Montado/servido': 'cascade'
        },
        compute='_compute_estado_recambio',
        store=True,
        readonly=False
    )

    @api.depends('location_dest_id', 'location_id', 'state', 'picked', 'purchase_line_id', 'repair_id')
    def _compute_estado_recambio(self):
        """
        Computa el estado del recambio basado en su ubicación y contexto
        """
        for record in self:
            try:
                estado = False
                
                _logger.info(f"Computing estado_recambio for move {record.id}: "
                           f"state={record.state}, picked={record.picked}, "
                           f"location_dest_id={record.location_dest_id.complete_name if record.location_dest_id else None}")
                
                # 1. Montado/servido: Si está marcado como picked o se ha usado
                if record.picked:
                    estado = 'Montado/servido'
                    _logger.info(f"Move {record.id}: Estado = Montado/servido (picked=True)")
                
                # 2. Verificar si el componente se ha usado en reparación
                elif record._is_component_used():
                    estado = 'Montado/servido'
                    _logger.info(f"Move {record.id}: Estado = Montado/servido (component used)")
                
                # 3. Pte almacenar: Recepción en 2 pasos, primera recepción desde compra
                elif record._is_pending_storage():
                    estado = 'Pte almacenar'
                    _logger.info(f"Move {record.id}: Estado = Pte almacenar")
                
                # 4. Estanteria: Ubicado en sub-ubicación de Stock
                elif record._is_in_shelf_location():
                    estado = 'Estanteria'
                    _logger.info(f"Move {record.id}: Estado = Estanteria")
                
                # 5. Stock: Ubicado en la ubicación padre Stock
                elif record._is_in_stock_location():
                    estado = 'Stock'
                    _logger.info(f"Move {record.id}: Estado = Stock")
                
                # 6. Estado por defecto para movimientos sin ubicación específica
                else:
                    # Si es un movimiento de reparación sin estado específico
                    if record.repair_id and record.state in ['assigned', 'partially_available']:
                        estado = 'Stock'  # Asumimos que está disponible en stock
                    _logger.info(f"Move {record.id}: Estado = {estado} (default)")
                
                record.estado_recambio = estado
                
            except Exception as e:
                _logger.error(f"Error computing estado_recambio for move {record.id}: {str(e)}")
                record.estado_recambio = False

    def _is_pending_storage(self):
        """
        Verifica si el movimiento está pendiente de almacenamiento
        """
        try:
            if not self.purchase_line_id or self.state not in ['assigned', 'partially_available', 'waiting']:
                return False
                
            # Si no hay ubicación de destino, no puede estar pendiente de almacenamiento
            if not self.location_dest_id:
                return False
                
            # Obtener el almacén de destino
            warehouse = self.location_dest_id.warehouse_id or self.location_dest_id._get_warehouse()
            if not warehouse:
                return False
                
            # Verificar si está configurado para recepción en 2 pasos
            if not hasattr(warehouse, 'reception_steps') or warehouse.reception_steps != 'two_steps':
                return False
                
            # Verificar si la ubicación de destino es la ubicación de entrada/input
            return self.location_dest_id == warehouse.wh_input_stock_loc_id
            
        except Exception as e:
            _logger.error(f"Error in _is_pending_storage for move {self.id}: {str(e)}")
            return False

    def _is_in_shelf_location(self):
        """
        Verifica si está en una sub-ubicación de Stock (estantería)
        """
        try:
            if not self.location_dest_id or self.state != 'done':
                return False
                
            # Obtener la ubicación de stock del almacén
            warehouse = self.location_dest_id.warehouse_id or self.location_dest_id._get_warehouse()
            if not warehouse:
                return False
                
            stock_location = warehouse.lot_stock_id
            if not stock_location:
                return False
            
            # Verificar si es una sub-ubicación de Stock pero no la ubicación Stock principal
            is_child = self.location_dest_id.location_id == stock_location
            is_not_main = self.location_dest_id != stock_location
            
            return is_child and is_not_main
            
        except Exception as e:
            _logger.error(f"Error in _is_in_shelf_location for move {self.id}: {str(e)}")
            return False

    def _is_in_stock_location(self):
        """
        Verifica si está en la ubicación padre Stock
        """
        try:
            if not self.location_dest_id or self.state != 'done':
                return False
                
            warehouse = self.location_dest_id.warehouse_id or self.location_dest_id._get_warehouse()
            if not warehouse:
                return False
                
            # Verificar si está exactamente en la ubicación Stock principal
            return self.location_dest_id == warehouse.lot_stock_id
            
        except Exception as e:
            _logger.error(f"Error in _is_in_stock_location for move {self.id}: {str(e)}")
            return False

    def _is_component_used(self):
        """
        Verifica si el componente se ha usado en una reparación o venta
        """
        try:
            # Verificar si está relacionado con una orden de reparación completada
            if self.repair_id:
                if self.repair_id.state in ['done', 'invoice']:
                    return True
                # Si es una línea de tipo 'add' en una reparación y el movimiento está hecho
                if (hasattr(self, 'repair_line_type') and 
                    self.repair_line_type == 'add' and 
                    self.state == 'done'):
                    return True
                    
            # Verificar si está en una orden de venta de reparación
            if (hasattr(self, 'sale_line_id') and self.sale_line_id and 
                hasattr(self.sale_line_id.order_id, 'repair_id') and 
                self.sale_line_id.order_id.repair_id):
                return True
                
            # Verificar si es un movimiento de salida desde stock hacia producción/uso
            if (self.location_id and self.location_dest_id and
                self.location_id.usage == 'internal' and 
                self.location_dest_id.usage in ['production', 'customer'] and
                self.state == 'done'):
                return True
                
            return False
            
        except Exception as e:
            _logger.error(f"Error in _is_component_used for move {self.id}: {str(e)}")
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
        trigger_fields = ['location_dest_id', 'location_id', 'state', 'picked', 'repair_id']
        
        if any(field in vals for field in trigger_fields):
            # Forzar recálculo
            self.invalidate_recordset(['estado_recambio'])
            
        return result
    
    @api.model
    def create(self, vals):
        """
        Override create para calcular el estado inicial
        """
        move = super().create(vals)
        # Forzar cálculo inicial del estado
        move._compute_estado_recambio()
        return move