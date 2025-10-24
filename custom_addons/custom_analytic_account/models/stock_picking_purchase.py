from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPickingPurchase(models.Model):
    """Lógica de distribución analítica para COMPRAS"""
    _inherit = 'stock.picking'

    def _process_incoming_picking(self, picking):
        """
        Procesa recepciones de compra (incoming).
        - Crea cuentas analíticas por lote/serie
        - Asigna distribución analítica en líneas de compra
        - NO procesa devoluciones de alquiler (eso es en rental)
        """
        # Excluir devoluciones de alquiler
        if self._is_rental_return(picking):
            return
        
        if not picking.move_line_ids or not picking.purchase_id:
            return
        
        # Recopilar lotes/series únicos
        lot_names = self._get_unique_lot_names(picking.move_line_ids)
        if not lot_names:
            return
        
        # Crear/obtener cuentas analíticas
        lot_to_account = self._create_or_get_analytic_accounts(lot_names)
        
        # Distribuir en líneas de compra
        self._distribute_analytic_in_purchase_lines(picking, lot_to_account)

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
        Retorna dict: {lot_name: account_record} (FIX: records, no IDs)
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
                lot_to_account[lot_name] = existing_account  # Record
                self._log_message('INFO', f'Cuenta analítica existente: {lot_name} (ID: {existing_account.id})')
            else:
                new_account = self.env['account.analytic.account'].create({
                    'name': f'RCT-{lot_name}',
                    'code': lot_name,
                    'partner_id': False,
                    'plan_id': analytic_plan.id,
                    'active': True,
                })
                lot_to_account[lot_name] = new_account  # Record directo
                self._log_message('INFO', f'Cuenta analítica creada: {lot_name} → {new_account.name} (ID: {new_account.id})')
        
        return lot_to_account

    def _get_default_analytic_plan(self):
        """Obtiene el plan analítico predefinido para la compañía."""
        return self.env['account.analytic.plan'].search([], limit=1)

    def _distribute_analytic_in_purchase_lines(self, picking, lot_to_account):
        """
        Distribuye las cuentas analíticas equitativamente en las líneas de compra.
        """
        distribution_data = self._group_qty_by_purchase_line_and_lot(picking.move_line_ids)
        
        for purchase_line_id, lot_qty_map in distribution_data.items():
            purchase_line = self.env['purchase.order.line'].browse(purchase_line_id)
            analytic_dist = self._calculate_analytic_distribution(
                lot_qty_map, lot_to_account, order_line=purchase_line
            )
            
            if analytic_dist:
                # FIX: Para compras, usa _apply_analytic_distribution (sobrescribe), no cumulative
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

    def _is_rental_return(self, picking):
        """Detecta si es devolución de alquiler."""
        return (
            picking.picking_type_id.code == 'incoming' 
            and picking.origin 
            and ('RENT' in picking.origin.upper() or '/rental.order/' in (picking.origin or ''))
        )