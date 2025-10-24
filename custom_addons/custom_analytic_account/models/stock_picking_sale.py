from odoo import api, models, _
import logging

_logger = logging.getLogger(__name__)


class StockPickingSale(models.Model):
    """Lógica de distribución analítica para VENTAS"""
    _inherit = 'stock.picking'

    def _process_outgoing_picking(self, picking):
        """
        Procesa entregas de venta (outgoing).
        - Asigna distribución analítica en líneas de venta según lote/serie entregado
        - Asigna cliente a cuenta analítica (venta definitiva)
        - NO procesa entregas de alquiler (eso es en rental)
        """
        # Excluir entregas de alquiler
        if self._is_rental_pickup(picking):
            return
        
        if not picking.move_line_ids:
            return
        
        sale_order = self._get_related_sale_order(picking)
        if not sale_order:
            self._log_message('WARNING', f'Picking {picking.name} sin orden de venta asociada')
            return
        
        # Distribuir en líneas de venta
        self._distribute_analytic_in_sale_lines(picking, sale_order)

    def _get_related_sale_order(self, picking):
        """Obtiene la orden de venta relacionada con el picking."""
        if picking.sale_id:
            return picking.sale_id
        
        if picking.origin:
            sale_order = self.env['sale.order'].search([
                ('name', '=', picking.origin)
            ], limit=1)
            return sale_order
        
        return False

    def _distribute_analytic_in_sale_lines(self, picking, sale_order):
        """
        Distribuye las cuentas analíticas en las líneas de venta según lotes/series entregados.
        """
        distribution_data = self._group_qty_by_sale_line_and_lot(picking.move_line_ids)
        
        for sale_line_id, lot_qty_map in distribution_data.items():
            sale_line = self.env['sale.order.line'].browse(sale_line_id)
            
            lot_to_account = self._get_analytic_accounts_by_lot_names(lot_qty_map.keys())
            
            if not lot_to_account:
                self._log_message('WARNING', 
                    f'No se encontraron cuentas analíticas para los lotes de la línea {sale_line.id}')
                continue
            
            analytic_dist = self._calculate_analytic_distribution(
                lot_qty_map, lot_to_account, order_line=sale_line
            )
            
            if analytic_dist:
                self._apply_analytic_distribution_cumulative(sale_line, analytic_dist, 'sale')
                
                # ASIGNAR CLIENTE A LAS CUENTAS ANALÍTICAS (venta definitiva)
                self._assign_partner_to_analytic_accounts(
                    lot_to_account.values(),  # FIX: Ya son records
                    sale_order.partner_id,
                    is_rental=False
                )

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
        Retorna: {lot_name: account_record} (FIX: records, no IDs)
        """
        lot_to_account = {}
        accounts = self.env['account.analytic.account'].search([
            ('code', 'in', list(lot_names))
        ])
        for acc in accounts:
            lot_to_account[acc.code] = acc  # Record
        
        return lot_to_account

    def _assign_partner_to_analytic_accounts(self, accounts, partner, is_rental=False):
        """
        Asigna cliente a cuentas analíticas.
        - Venta definitiva: siempre asigna
        - Alquiler: solo asigna si está vacío (no sobrescribe)
        
        FIX: accounts ya son records (iterable de records)
        """
        for account in accounts:
            if is_rental:
                # Alquiler: solo asignar si está vacío
                if not account.partner_id:
                    account.write({'partner_id': partner.id})
                    self._log_message('INFO', f'Cliente {partner.name} asignado a cuenta {account.code} (alquiler)')
            else:
                # Venta definitiva: siempre asignar
                account.write({'partner_id': partner.id})
                self._log_message('INFO', f'Cliente {partner.name} asignado a cuenta {account.code} (venta)')

    def _is_rental_pickup(self, picking):
        """Detecta si es entrega de alquiler."""
        return (
            picking.picking_type_id.code == 'outgoing' 
            and picking.origin 
            and ('RENT' in picking.origin.upper() or '/rental.order/' in (picking.origin or ''))
        )