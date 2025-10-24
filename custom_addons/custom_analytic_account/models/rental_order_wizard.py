from odoo import api, models, _
import logging

_logger = logging.getLogger(__name__)

class RentalOrderWizardLine(models.TransientModel):
    """Capturar datos de las líneas ANTES de que el wizard las procese"""
    _inherit = 'rental.order.wizard.line'
    
    def write(self, vals):
        """Interceptar cuando se asignan lotes en el wizard"""
        res = super().write(vals)
        
        # Si se está asignando un lote/serie
        if 'lot_id' in vals and vals['lot_id']:
            _logger.info(f'[WIZARD LINE] Lote asignado: {self.lot_id.name} - Cantidad: {self.product_uom_qty}')
        
        return res

class StockMove(models.Model):
    """Procesar en el momento en que se valida el movimiento de stock"""
    _inherit = 'stock.move'
    
    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        
        rental_moves = self.filtered(lambda m: 
            m.sale_line_id and 
            m.sale_line_id.order_id and
            m.sale_line_id.order_id.is_rental_order
        )
        
        for move in rental_moves:
            _logger.info(f'[RENTAL MOVE] {move.reference}')
            _logger.info(f'  - Origen: {move.location_id.name} (usage: {move.location_id.usage})')
            _logger.info(f'  - Destino: {move.location_dest_id.name} (usage: {move.location_dest_id.usage})')
            _logger.info(f'  - Picking ID: {move.picking_id.name if move.picking_id else "None"}')
            _logger.info(f'  - Tipo picking: {move.picking_type_id.code if move.picking_type_id else "N/A"}')
            
            try:
                # Detección principal: por picking_type (si existe)
                if move.picking_type_id:
                    if move.picking_type_id.code == 'outgoing':
                        _logger.info('  → ES ENTREGA (por picking)')
                        self._process_rental_delivery(move)
                    elif move.picking_type_id.code == 'incoming':
                        _logger.info('  → ES DEVOLUCIÓN (por picking)')
                        self._process_rental_return(move)
                else:
                    # Fallback: Por nombres de ubicación (específico para flujos internos de rental)
                    origin_name = move.location_id.name.lower()
                    dest_name = move.location_dest_id.name.lower()
                    
                    if 'stock' in origin_name and 'rental' in dest_name:
                        _logger.info('  → ES ENTREGA (por ubicación: Stock → Rental)')
                        self._process_rental_delivery(move)
                    elif 'rental' in origin_name and 'stock' in dest_name:
                        _logger.info('  → ES DEVOLUCIÓN (por ubicación: Rental → Stock)')
                        self._process_rental_return(move)
                    else:
                        # Fallback adicional: Por usage (para flujos con customer, si aplica)
                        if move.location_dest_id.usage == 'customer':
                            _logger.info('  → ES ENTREGA (por usage: a customer)')
                            self._process_rental_delivery(move)
                        elif move.location_id.usage == 'customer':
                            _logger.info('  → ES DEVOLUCIÓN (por usage: desde customer)')
                            self._process_rental_return(move)
                        else:
                            _logger.warning(f'  ⚠ Ubicación no reconocida: {move.location_id.name} → {move.location_dest_id.name} (usages: {move.location_id.usage} → {move.location_dest_id.usage})')
            except Exception as e:
                _logger.error(f'Error procesando movimiento {move.reference}: {str(e)}')
        
        return res
        
    def _process_rental_delivery(self, move):
        """Procesar entregas de alquiler"""
        if not move.move_line_ids:
            _logger.warning(f'No se encontraron move lines en el movimiento {move.reference}')
            return
        
        sale_line = move.sale_line_id
        rental_order = sale_line.order_id
        
        # Agrupar cantidades por lote
        lot_qty_map = {}
        for ml in move.move_line_ids:
            if ml.lot_id:
                lot_name = ml.lot_id.name
                lot_qty_map[lot_name] = lot_qty_map.get(lot_name, 0) + ml.quantity
        
        if not lot_qty_map:
            _logger.warning(f'No se encontraron lotes en el movimiento {move.reference}')
            return
        
        # Obtener cuentas analíticas usando el método helper
        lot_to_account = self._get_analytic_accounts_by_lot_names(lot_qty_map.keys())
        
        if not lot_to_account:
            _logger.warning(f'No se encontraron cuentas analíticas para lotes: {list(lot_qty_map.keys())}')
            return
        
        # Calcular distribución
        total_qty = sum(lot_qty_map.values())
        distribution = {}
        
        for lot_name, qty in lot_qty_map.items():
            account = lot_to_account.get(lot_name)
            if account:
                percentage = round((qty / total_qty) * 100, 2)
                distribution[str(account.id)] = percentage
        
        if distribution:
            sale_line.write({'analytic_distribution': distribution})
            _logger.info(f'✓ Distribución aplicada: {distribution}')
            
            # Asignar cliente a cuentas
            for account in lot_to_account.values():
                if not account.partner_id:
                    account.write({'partner_id': rental_order.partner_id.id})
                    _logger.info(f'✓ Cliente asignado a cuenta {account.code}')
    
    def _process_rental_return(self, move):
        """Procesar devoluciones de alquiler"""
        if not move.move_line_ids:
            _logger.warning(f'No se encontraron move lines en el movimiento {move.reference}')
            return
        
        for ml in move.move_line_ids:
            if ml.lot_id:
                lot_names = [ml.lot_id.name]  # Para usar el helper
                lot_to_account = self._get_analytic_accounts_by_lot_names(lot_names)
                account = lot_to_account.get(ml.lot_id.name)
                
                if account and account.partner_id:
                    account.write({'partner_id': False})
                    _logger.info(f'✓ Cliente limpiado de cuenta {account.code}')
    
    def _get_analytic_accounts_by_lot_names(self, lot_names):
        """Mapea lotes a cuentas analíticas"""
        accounts = self.env['account.analytic.account'].search([
            ('code', 'in', list(lot_names))
        ])
        return {acc.code: acc for acc in accounts}