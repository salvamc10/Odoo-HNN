from odoo import api, models, _
import logging

_logger = logging.getLogger(__name__)


class StockPickingCommon(models.Model):
    """Métodos comunes y punto de entrada principal para distribución analítica"""
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Override del método de validación de picking.
        Aplica lógica de analítica automática según el tipo de operación.
        """
        res = super(StockPickingCommon, self).button_validate()
        
        # Procesar solo pickings validados
        for picking in self.filtered(lambda p: p.state == 'done'):
            try:
                # Routing según tipo de operación
                if picking.picking_type_id.code == 'incoming':
                    # Compras o devoluciones de alquiler
                    if self._is_rental_return(picking):
                        self._process_rental_incoming_picking(picking)
                    else:
                        self._process_incoming_picking(picking)
                
                elif picking.picking_type_id.code == 'outgoing':
                    # Ventas o entregas de alquiler
                    if self._is_rental_pickup(picking):
                        self._process_rental_outgoing_picking(picking)
                    else:
                        self._process_outgoing_picking(picking)
                
            except Exception as e:
                _logger.error(f"Error procesando picking {picking.name}: {str(e)}")
                self._log_message('ERROR', f'Error en picking {picking.name}: {str(e)}')
        
        # Lógica original de batches y backorders
        self._handle_batches_and_backorders()
        
        return res

    # ============================================================================
    # MÉTODOS COMUNES DE DISTRIBUCIÓN ANALÍTICA
    # ============================================================================

    def _calculate_analytic_distribution(self, lot_qty_map, lot_to_account, order_line=None):
        """
        Calcula la distribución analítica proporcional según cantidades.
        
        Args:
            lot_qty_map: {lot_name: qty}
            lot_to_account: {lot_name: account_id}
            order_line: Línea de pedido (ventas) o None (compras)
        
        Returns:
            {account_id_str: percentage} - Suma exacta 100%
        """
        # Determinar cantidad total
        if order_line and hasattr(order_line, 'product_uom_qty'):
            # VENTAS: usar cantidad total pedida (para entregas parciales)
            total_qty = order_line.product_uom_qty
        else:
            # COMPRAS: usar suma de cantidades entregadas
            total_qty = sum(lot_qty_map.values())
        
        if total_qty == 0:
            return {}
        
        analytic_dist = {}
        
        # Calcular porcentajes
        for lot_name, qty in lot_qty_map.items():
            account_id = lot_to_account.get(lot_name)
            if account_id:
                percentage = (qty / total_qty) * 100
                analytic_dist[str(account_id)] = percentage
        
        if not analytic_dist:
            return {}
        
        # Ajustar para que sume exactamente 100% (solo para compras)
        if not order_line:
            current_sum = sum(analytic_dist.values())
            if abs(current_sum - 100.0) > 0.01:
                last_account = list(analytic_dist.keys())[-1]
                analytic_dist[last_account] += (100.0 - current_sum)
        
        return analytic_dist

    def _apply_analytic_distribution(self, order_line, analytic_dist, operation_type):
        """
        Aplica la distribución analítica a una línea de pedido (COMPRAS).
        Sobrescribe completamente la distribución anterior.
        
        Args:
            order_line: purchase.order.line
            analytic_dist: {account_id_str: percentage}
            operation_type: 'purchase'
        """
        suma_porcentajes = sum(analytic_dist.values())
        
        self._log_message('DEBUG', 
            f'{operation_type.upper()} Line {order_line.id}: Distribución={analytic_dist}, Suma={suma_porcentajes:.2f}%')
        
        if abs(suma_porcentajes - 100.0) < 0.1:
            order_line.write({'analytic_distribution': analytic_dist})
            
            self._log_message('INFO', 
                f'Distribución aplicada en {operation_type} line {order_line.id}: {analytic_dist} (suma: {suma_porcentajes:.2f}%)')
        else:
            self._log_message('ERROR', 
                f'{operation_type.upper()} Line {order_line.id}: Suma={suma_porcentajes:.2f}% != 100%. No aplicado.')

    def _apply_analytic_distribution_cumulative(self, order_line, analytic_dist, operation_type):
        """
        Aplica distribución analítica de forma acumulativa (VENTAS con entregas parciales).
        Suma a la distribución existente y normaliza a 100%.
        
        Args:
            order_line: sale.order.line
            analytic_dist: {account_id_str: percentage}
            operation_type: 'sale'
        """
        # Obtener distribución actual
        current_dist = order_line.analytic_distribution or {}
        
        # SUMAR nueva distribución a la existente
        merged_dist = {}
        all_accounts = set(current_dist.keys()) | set(analytic_dist.keys())
        
        for account_id_str in all_accounts:
            current_value = current_dist.get(account_id_str, 0.0)
            new_value = analytic_dist.get(account_id_str, 0.0)
            merged_dist[account_id_str] = current_value + new_value
        
        # Normalizar a 100%
        total = sum(merged_dist.values())
        if total > 0:
            normalized_dist = {k: (v / total) * 100 for k, v in merged_dist.items()}
            order_line.write({'analytic_distribution': normalized_dist})
            
            self._log_message('INFO', 
                f'Distribución acumulada en {operation_type} line {order_line.id}: {normalized_dist}')
        else:
            self._log_message('ERROR', 
                f'{operation_type} line {order_line.id}: Total acumulado es 0, no se aplicó distribución')

    # ============================================================================
    # MÉTODOS DE UTILIDAD Y LOGGING
    # ============================================================================

    def _log_message(self, level, message):
        """
        Registra mensajes en el logger de Python.
        
        Args:
            level: 'INFO', 'WARNING', 'ERROR', 'DEBUG'
            message: Texto del mensaje
        """
        log_method = getattr(_logger, level.lower(), _logger.info)
        log_method(message)

    def _handle_batches_and_backorders(self):
        """
        Lógica original de Odoo para manejar batches y backorders.
        Separado en método para claridad.
        """
        to_assign_ids = set()
        
        if not any(picking.state == 'done' for picking in self):
            return
        
        if self and self.env.context.get('pickings_to_detach'):
            pickings_to_detach = self.env['stock.picking'].browse(self.env.context['pickings_to_detach'])
            pickings_to_detach.batch_id = False
            pickings_to_detach.move_ids.filtered(lambda m: not m.quantity).picked = False
            to_assign_ids.update(self.env.context['pickings_to_detach'])

        for picking in self:
            if picking.state != 'done':
                continue
            if picking.batch_id and any(p.state != 'done' for p in picking.batch_id.picking_ids):
                picking.batch_id = None
            to_assign_ids.update(picking.backorder_ids.ids)

        assignable_pickings = self.env['stock.picking'].browse(to_assign_ids)
        for picking in assignable_pickings:
            if hasattr(picking, '_find_auto_batch'):
                picking._find_auto_batch()
        
        assignable_pickings.move_line_ids.with_context(skip_auto_waveable=True)._auto_wave()