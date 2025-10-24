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
        Calcula % basado en PROPORCIÓN de lotes en el pedido total, NO en qty_done.
        
        Ejemplo: Pedido 3 ud con lotes [A, B, C]
        - Entrega 1: 2 ud [A, B] → A:33.33%, B:33.33% (no 50/50)
        - Entrega 2: 1 ud [C] → C:33.33%
        - Total acumulado: 100%
        
        FIX: Si lot_to_account tiene ints (IDs), browse a records.
        """
        if not order_line:
            # Sin order_line, reparto equitativo entre lotes
            total_qty = sum(lot_qty_map.values())
        else:
            # Con order_line, usar cantidad TOTAL del pedido
            total_qty = getattr(order_line, 'product_qty', getattr(order_line, 'product_uom_qty', 0))
        
        if total_qty == 0:
            return {}
        
        # FIX: Asegurar que lot_to_account tiene records (no IDs)
        fixed_lot_to_account = {}
        for lot_name, account in lot_to_account.items():
            if isinstance(account, int):
                account_rec = self.env['account.analytic.account'].browse(account)
                if account_rec.exists():
                    fixed_lot_to_account[lot_name] = account_rec
                    _logger.info(f'  - Convertido ID {account} a record para {lot_name}')
                else:
                    _logger.warning(f'Cuenta ID {account} no existe para {lot_name}')
                    continue
            else:
                fixed_lot_to_account[lot_name] = account
        
        lot_to_account = fixed_lot_to_account
        
        analytic_dist = {}
        for lot_name, qty_done in lot_qty_map.items():
            account = lot_to_account.get(lot_name)
            if account:
                # Porcentaje = cantidad de este lote / cantidad total pedida (fijo, parcial OK)
                percentage = round((qty_done / total_qty) * 100, 2)
                analytic_dist[str(account.id)] = percentage
        
        _logger.info(f'  - Distribución calculada para esta entrega: {analytic_dist} (total_qty: {total_qty}, qty_this: {sum(lot_qty_map.values())})')
        return analytic_dist
        
    def _apply_analytic_distribution(self, order_line, analytic_dist, operation_type):
        """
        Aplica la distribución analítica de forma ACUMULATIVA (para COMPRAS con recepciones parciales).
        Agrega % nuevos a existentes, SIN normalizar (suma natural a 100% al final).
        No check de 100%: Aplica parciales, Odoo prorratea.
        
        Args:
            order_line: purchase.order.line
            analytic_dist: {account_id_str: percentage} (parcial)
            operation_type: 'purchase'
        """
        if not analytic_dist:
            return
        
        # Obtener distribución actual
        current_dist = order_line.analytic_distribution or {}
        
        # AGREGAR nueva distribución a la existente (sin tocar previos)
        merged_dist = current_dist.copy()
        for acc_id_str, percentage in analytic_dist.items():
            if acc_id_str in merged_dist:
                merged_dist[acc_id_str] += percentage  # Acumula si lote repetido (raro)
            else:
                merged_dist[acc_id_str] = percentage
        
        suma_porcentajes = sum(merged_dist.values())
        
        self._log_message('DEBUG', 
            f'{operation_type.upper()} Line {order_line.id}: Nueva dist={analytic_dist}, Acumulada={merged_dist}, Suma total={suma_porcentajes:.2f}%')
        
        # Siempre aplica (parcial OK, suma crece a 100%)
        order_line.write({'analytic_distribution': merged_dist})
        
        self._log_message('INFO', 
            f'Distribución acumulada aplicada en {operation_type} line {order_line.id}: {merged_dist} (suma: {suma_porcentajes:.2f}%)')

    def _apply_analytic_distribution_cumulative(self, order_line, analytic_dist, operation_type):
        """
        Aplica distribución analítica de forma acumulativa (VENTAS con entregas parciales).
        Agrega % nuevos a existentes, SIN normalizar (suma natural a 100% al final).
        
        Args:
            order_line: sale.order.line
            analytic_dist: {account_id_str: percentage} (parcial)
            operation_type: 'sale'
        """
        if not analytic_dist:
            return
        
        # Obtener distribución actual
        current_dist = order_line.analytic_distribution or {}
        
        # AGREGAR nueva distribución a la existente (sin tocar previos)
        merged_dist = current_dist.copy()
        for acc_id_str, percentage in analytic_dist.items():
            if acc_id_str in merged_dist:
                merged_dist[acc_id_str] += percentage  # Acumula si lote repetido
            else:
                merged_dist[acc_id_str] = percentage
        
        suma_porcentajes = sum(merged_dist.values())
        
        self._log_message('DEBUG', 
            f'{operation_type.upper()} Line {order_line.id}: Nueva dist={analytic_dist}, Acumulada={merged_dist}, Suma total={suma_porcentajes:.2f}%')
        
        # Siempre aplica (parcial OK)
        order_line.write({'analytic_distribution': merged_dist})
        
        self._log_message('INFO', 
            f'Distribución acumulada aplicada en {operation_type} line {order_line.id}: {merged_dist} (suma: {suma_porcentajes:.2f}%)')

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