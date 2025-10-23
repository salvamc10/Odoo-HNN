from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Override del método de validación de picking.
        Aplica lógica de analítica automática según el tipo de operación.
        """
        res = super(StockPicking, self).button_validate()
        
        # Procesar solo pickings validados
        for picking in self.filtered(lambda p: p.state == 'done'):
            try:
                # Routing según tipo de operación
                if picking.picking_type_id.code == 'incoming':
                    self._process_incoming_picking(picking)
                elif picking.picking_type_id.code == 'outgoing':
                    self._process_outgoing_picking(picking)
                # Agregar más tipos si es necesario (internal, etc.)
            except Exception as e:
                _logger.error(f"Error procesando picking {picking.name}: {str(e)}")
                self._log_message('ERROR', f'Error en picking {picking.name}: {str(e)}')
        
        # Lógica original de batches y backorders
        self._handle_batches_and_backorders()
        
        return res

    # ============================================================================
    # MÉTODOS PARA RECEPCIONES (COMPRAS) - Sprint 1 y 2
    # ============================================================================

    def _process_incoming_picking(self, picking):
        """
        Procesa recepciones de compra (incoming).
        - Crea cuentas analíticas por lote/serie
        - Asigna distribución analítica en líneas de compra
        """
        if not picking.move_line_ids:
            return
        
        # Recopilar lotes/series únicos
        lot_names = self._get_unique_lot_names(picking.move_line_ids)
        if not lot_names:
            return
        
        # Crear/obtener cuentas analíticas
        lot_to_account = self._create_or_get_analytic_accounts(lot_names)
        
        # Distribuir en líneas de compra si existe purchase_id
        if picking.purchase_id:
            self._distribute_analytic_in_purchase_lines(picking, lot_to_account)
        else:
            self._log_message('WARNING', f'Picking {picking.name} sin orden de compra asociada')

    def _get_unique_lot_names(self, move_lines):
        """Extrae nombres únicos de lotes/series de las líneas de movimiento."""
        lot_names = set()
        for move_line in move_lines:
            if move_line.lot_id and move_line.qty_done > 0:
                lot_names.add(move_line.lot_id.name)
        return lot_names

    def _create_or_get_analytic_accounts(self, lot_names):
        """
        Crea o recupera cuentas analíticas para cada lote/serie.
        Retorna dict: {lot_name: account_id}
        """
        lot_to_account = {}
        analytic_plan = self._get_default_analytic_plan()
        
        if not analytic_plan:
            raise UserError(_('No se encontró un plan analítico predefinido.'))
        
        for lot_name in lot_names:
            existing_account = self.env['account.analytic.account'].search([
                ('code', '=', lot_name),
            ], limit=1)
            
            if existing_account:
                lot_to_account[lot_name] = existing_account.id
                self._log_message('INFO', f'Cuenta analítica existente: {lot_name} (ID: {existing_account.id})')
            else:
                new_account = self.env['account.analytic.account'].create({
                    'name': f'RCT-{lot_name}',
                    'code': lot_name,
                    'partner_id': False,
                    'plan_id': analytic_plan.id,
                    'active': True,
                })
                lot_to_account[lot_name] = new_account.id
                self._log_message('INFO', f'Cuenta analítica creada: {lot_name} → {new_account.name} (ID: {new_account.id})')
        
        return lot_to_account

    def _get_default_analytic_plan(self):
        """Obtiene el plan analítico predefinido para la compañía."""
        # TODO: Implementar lógica de configuración por compañía (HU3)
        return self.env['account.analytic.plan'].search([], limit=1)

    def _distribute_analytic_in_purchase_lines(self, picking, lot_to_account):
        """
        Distribuye las cuentas analíticas equitativamente en las líneas de compra.
        """
        # Agrupar qty_done por purchase_line_id y lot_name
        distribution_data = self._group_qty_by_purchase_line_and_lot(picking.move_line_ids)
        
        # Aplicar distribución a cada línea de compra
        for purchase_line_id, lot_qty_map in distribution_data.items():
            purchase_line = self.env['purchase.order.line'].browse(purchase_line_id)
            analytic_dist = self._calculate_analytic_distribution(lot_qty_map, lot_to_account)
            
            if analytic_dist:
                self._apply_analytic_distribution(purchase_line, analytic_dist, 'purchase')

    def _group_qty_by_purchase_line_and_lot(self, move_lines):
        """
        Agrupa cantidades por línea de compra y lote.
        Retorna: {purchase_line_id: {lot_name: qty_done}}
        """
        distribution_data = {}
        
        for move_line in move_lines:
            if not (move_line.lot_id and move_line.qty_done > 0 and move_line.move_id.purchase_line_id):
                continue
            
            purchase_line_id = move_line.move_id.purchase_line_id.id
            lot_name = move_line.lot_id.name
            
            if purchase_line_id not in distribution_data:
                distribution_data[purchase_line_id] = {}
            if lot_name not in distribution_data[purchase_line_id]:
                distribution_data[purchase_line_id][lot_name] = 0.0
            
            distribution_data[purchase_line_id][lot_name] += move_line.qty_done
        
        return distribution_data

    # ============================================================================
    # MÉTODOS PARA ENTREGAS (VENTAS) - Sprint 4 (HU5)
    # ============================================================================

    def _process_outgoing_picking(self, picking):
        """
        Procesa entregas de venta (outgoing).
        - Asigna distribución analítica en líneas de venta según lote/serie entregado
        """
        if not picking.move_line_ids:
            return
        
        # Obtener el documento origen (sale.order o sale.rental)
        sale_order = self._get_related_sale_order(picking)
        if not sale_order:
            self._log_message('WARNING', f'Picking {picking.name} sin orden de venta/alquiler asociada')
            return
        
        # Distribuir en líneas de venta/alquiler
        self._distribute_analytic_in_sale_lines(picking, sale_order)

    def _get_related_sale_order(self, picking):
        """Obtiene la orden de venta relacionada con el picking."""
        if picking.sale_id:
            return picking.sale_id
        
        # Buscar por origin si no está en sale_id
        if picking.origin:
            sale_order = self.env['sale.order'].search([
                ('name', '=', picking.origin)
            ], limit=1)
            return sale_order
        
        return False

    def _distribute_analytic_in_sale_lines(self, picking, sale_order):
        distribution_data = self._group_qty_by_sale_line_and_lot(picking.move_line_ids)
        
        for sale_line_id, lot_qty_map in distribution_data.items():
            sale_line = self.env['sale.order.line'].browse(sale_line_id)
            lot_to_account = self._get_analytic_accounts_by_lot_names(lot_qty_map.keys())
            
            if not lot_to_account:
                continue
            
            # PASAR sale_line para calcular sobre qty total
            analytic_dist = self._calculate_analytic_distribution(
                lot_qty_map, lot_to_account, order_line=sale_line
            )
            
            if analytic_dist:
                self._apply_analytic_distribution_cumulative(sale_line, analytic_dist, 'sale')

    # def _distribute_analytic_in_sale_lines(self, picking, sale_order):
    #     
    #     # Agrupar qty_done por sale_line_id y lot_name
    #     distribution_data = self._group_qty_by_sale_line_and_lot(picking.move_line_ids)
        
    #     # Aplicar distribución a cada línea de venta
    #     for sale_line_id, lot_qty_map in distribution_data.items():
    #         sale_line = self.env['sale.order.line'].browse(sale_line_id)
            
    #         # Buscar cuentas analíticas por código (lot_name)
    #         lot_to_account = self._get_analytic_accounts_by_lot_names(lot_qty_map.keys())
            
    #         if not lot_to_account:
    #             self._log_message('WARNING', 
    #                 f'No se encontraron cuentas analíticas para los lotes de la línea {sale_line.id}')
    #             continue
            
    #         analytic_dist = self._calculate_analytic_distribution(lot_qty_map, lot_to_account)
            
    #         if analytic_dist:
    #             self._apply_analytic_distribution(sale_line, analytic_dist, 'sale')

    def _group_qty_by_sale_line_and_lot(self, move_lines):
        """
        Agrupa cantidades por línea de venta y lote.
        Retorna: {sale_line_id: {lot_name: qty_done}}
        """
        distribution_data = {}
        
        for move_line in move_lines:
            if not (move_line.lot_id and move_line.qty_done > 0 and move_line.move_id.sale_line_id):
                continue
            
            sale_line_id = move_line.move_id.sale_line_id.id
            lot_name = move_line.lot_id.name
            
            if sale_line_id not in distribution_data:
                distribution_data[sale_line_id] = {}
            if lot_name not in distribution_data[sale_line_id]:
                distribution_data[sale_line_id][lot_name] = 0.0
            
            distribution_data[sale_line_id][lot_name] += move_line.qty_done
        
        return distribution_data

    def _get_analytic_accounts_by_lot_names(self, lot_names):
        """
        Busca cuentas analíticas por código (lot_name).
        Retorna: {lot_name: account_id}
        """
        lot_to_account = {}
        
        for lot_name in lot_names:
            account = self.env['account.analytic.account'].search([
                ('code', '=', lot_name),
            ], limit=1)
            
            if account:
                lot_to_account[lot_name] = account.id
        
        return lot_to_account

    # ============================================================================
    # MÉTODOS COMUNES DE DISTRIBUCIÓN ANALÍTICA
    # ============================================================================

    def _calculate_analytic_distribution(self, lot_qty_map, lot_to_account, order_line=None):
        """
        Calcula distribución sobre qty TOTAL del pedido, no sobre qty_done parcial.
        """
        # Obtener cantidad TOTAL de la línea de pedido
        if order_line:
            total_qty = order_line.product_uom_qty  # Cantidad total pedida
        else:
            total_qty = sum(lot_qty_map.values())  # Fallback para compras
        
        if total_qty == 0:
            return {}
        
        analytic_dist = {}
        
        # Calcular porcentajes sobre TOTAL del pedido
        for lot_name, qty in lot_qty_map.items():
            account_id = lot_to_account.get(lot_name)
            if account_id:
                percentage = (qty / total_qty) * 100
                analytic_dist[account_id] = percentage
        
        return analytic_dist

    # def _calculate_analytic_distribution(self, lot_qty_map, lot_to_account):
    #  
    #     total_qty = sum(lot_qty_map.values())
    #     if total_qty == 0:
    #         return {}
        
    #     analytic_dist = {}
        
    #     # Calcular porcentajes sin redondear
    #     for lot_name, qty in lot_qty_map.items():
    #         account_id = lot_to_account.get(lot_name)
    #         if account_id:
    #             percentage = (qty / total_qty) * 100
    #             analytic_dist[account_id] = percentage
        
    #     if not analytic_dist:
    #         return {}
        
    #     # Ajustar para que sume exactamente 100%
    #     current_sum = sum(analytic_dist.values())
    #     if abs(current_sum - 100.0) > 0.01:
    #         last_account = list(analytic_dist.keys())[-1]
    #         analytic_dist[last_account] += (100.0 - current_sum)
        
    #     return analytic_dist

    def _apply_analytic_distribution_cumulative(self, order_line, analytic_dist, operation_type):
        """
        Acumula distribución sin normalizar (cada entrega suma su % real).
        """
        current_dist = order_line.analytic_distribution or {}
        
        # SUMAR porcentajes reales
        merged_dist = dict(current_dist)
        for account_id, percentage in analytic_dist.items():
            account_str = str(account_id)
            merged_dist[account_str] = merged_dist.get(account_str, 0.0) + percentage
        
        order_line.write({'analytic_distribution': merged_dist})
        self._log_message('INFO', f'Distribución acumulada: {merged_dist}')

    # def _apply_analytic_distribution(self, order_line, analytic_dist, operation_type):
   
    #     suma_porcentajes = sum(analytic_dist.values())
        
    #     # Log de debug
    #     self._log_message('DEBUG', 
    #         f'{operation_type.upper()} Line {order_line.id}: Distribución={analytic_dist}, Suma={suma_porcentajes:.2f}%')
        
    #     # Validar que suma sea 100%
    #     if abs(suma_porcentajes - 100.0) < 0.1:
    #         # Reset completo - evita dilución de distribuciones previas
    #         order_line.write({'analytic_distribution': analytic_dist})
            
    #         self._log_message('INFO', 
    #             f'Distribución aplicada en {operation_type} line {order_line.id}: {analytic_dist} (suma: {suma_porcentajes:.2f}%)')
    #     else:
    #         self._log_message('ERROR', 
    #             f'{operation_type.upper()} Line {order_line.id}: Suma={suma_porcentajes:.2f}% != 100%. No aplicado.')

    # ============================================================================
    # MÉTODOS DE UTILIDAD Y LOGGING
    # ============================================================================

    def _log_message(self, level, message):
        """
        Registra mensajes en ir.logging y en el logger de Python.
        
        Args:
            level: 'INFO', 'WARNING', 'ERROR', 'DEBUG'
            message: Texto del mensaje
        """
        # Log en Python logger
        log_method = getattr(_logger, level.lower(), _logger.info)
        log_method(message)
        
        # Log en ir.logging (opcional, para auditoría en BD)
        # Comentar si genera demasiados registros
        # self.env['ir.logging'].sudo().create({
        #     'name': f'Analytic Distribution - {level}',
        #     'type': 'server',
        #     'level': level,
        #     'message': message,
        #     'path': 'stock.picking',
        #     'func': 'button_validate',
        #     'line': '1',
        # })

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