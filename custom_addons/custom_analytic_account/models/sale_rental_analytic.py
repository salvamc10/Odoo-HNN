from odoo import api, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleRental(models.Model):
    """Lógica de distribución analítica para ALQUILERES"""
    _inherit = 'sale.rental'

    def action_open_pickup(self):
        """
        Override: Al recoger productos de alquiler (asignar lotes/series).
        - Asigna distribución analítica proporcional en líneas de alquiler
        - Asigna cliente a cuenta analítica (solo si está vacío)
        """
        res = super(SaleRental, self).action_open_pickup()
        
        # Procesar después de que se asignen los lotes/series
        for rental in self:
            if rental.pickup_picking_id and rental.pickup_picking_id.state == 'done':
                rental._process_rental_pickup()
        
        return res

    def action_open_return(self):
        """
        Override: Al devolver productos de alquiler.
        - Limpia el cliente de la cuenta analítica
        - NO modifica la distribución analítica (ya está facturada)
        """
        res = super(SaleRental, self).action_open_return()
        
        for rental in self:
            if rental.return_picking_id and rental.return_picking_id.state == 'done':
                rental._process_rental_return()
        
        return res

    def _process_rental_pickup(self):
        """
        Procesa recogida de alquiler:
        1. Asigna distribución analítica proporcional en líneas
        2. Asigna cliente a cuentas analíticas
        """
        self.ensure_one()
        
        picking = self.pickup_picking_id
        if not picking or not picking.move_line_ids:
            return
        
        # Agrupar por línea de alquiler y lote
        distribution_data = self._group_rental_qty_by_line_and_lot(picking.move_line_ids)
        
        for rental_line_id, lot_qty_map in distribution_data.items():
            rental_line = self.env['sale.rental.schedule'].browse(rental_line_id)
            
            # Buscar cuentas analíticas por lote
            lot_to_account = self._get_analytic_accounts_by_lot_names(lot_qty_map.keys())
            
            if not lot_to_account:
                _logger.warning(f'No se encontraron cuentas analíticas para lotes de línea {rental_line.id}')
                continue
            
            # Calcular distribución proporcional
            analytic_dist = self._calculate_rental_analytic_distribution(
                lot_qty_map, lot_to_account, rental_line
            )
            
            if analytic_dist:
                # Aplicar distribución (directo, no acumulativo)
                self._apply_rental_analytic_distribution(rental_line, analytic_dist)
                
                # Asignar cliente a cuentas (solo si están vacías)
                self._assign_partner_to_rental_accounts(
                    lot_to_account.values(), 
                    self.partner_id
                )

    def _process_rental_return(self):
        """
        Procesa devolución de alquiler:
        - Limpia el cliente de las cuentas analíticas
        """
        self.ensure_one()
        
        picking = self.return_picking_id
        if not picking or not picking.move_line_ids:
            return
        
        # Obtener lotes devueltos
        lot_names = set()
        for move_line in picking.move_line_ids:
            if move_line.lot_id and move_line.qty_done > 0:
                lot_names.add(move_line.lot_id.name)
        
        # Limpiar cliente de cuentas analíticas
        for lot_name in lot_names:
            account = self.env['account.analytic.account'].search([
                ('code', '=', lot_name),
            ], limit=1)
            
            if account and account.partner_id:
                account.write({'partner_id': False})
                _logger.info(f'Cliente limpiado de cuenta {lot_name} (devolución alquiler {self.name})')

    def _group_rental_qty_by_line_and_lot(self, move_lines):
        """
        Agrupa cantidades por línea de alquiler y lote.
        Retorna: {rental_line_id: {lot_name: qty_done}}
        """
        distribution_data = {}
        
        for move_line in move_lines:
            # Buscar línea de alquiler relacionada
            rental_line = self._find_rental_line_for_move(move_line)
            
            if not rental_line or not move_line.lot_id or move_line.qty_done <= 0:
                continue
            
            rental_line_id = rental_line.id
            lot_name = move_line.lot_id.name
            
            if rental_line_id not in distribution_data:
                distribution_data[rental_line_id] = {}
            if lot_name not in distribution_data[rental_line_id]:
                distribution_data[rental_line_id][lot_name] = 0.0
            
            distribution_data[rental_line_id][lot_name] += move_line.qty_done
        
        return distribution_data

    def _find_rental_line_for_move(self, move_line):
        """
        Busca la línea de alquiler asociada al movimiento.
        Puede ser por sale_line_id o por product_id.
        """
        if move_line.move_id.sale_line_id:
            # Buscar por sale_line_id
            rental_line = self.env['sale.rental.schedule'].search([
                ('rental_id', '=', self.id),
                ('sale_order_line_id', '=', move_line.move_id.sale_line_id.id),
            ], limit=1)
            
            if rental_line:
                return rental_line
        
        # Buscar por product_id
        rental_line = self.env['sale.rental.schedule'].search([
            ('rental_id', '=', self.id),
            ('product_id', '=', move_line.product_id.id),
        ], limit=1)
        
        return rental_line

    def _calculate_rental_analytic_distribution(self, lot_qty_map, lot_to_account, rental_line):
        """
        Calcula distribución analítica proporcional para alquiler.
        Basado en cantidad total de la línea de alquiler.
        """
        total_qty = rental_line.product_uom_qty if hasattr(rental_line, 'product_uom_qty') else sum(lot_qty_map.values())
        
        if total_qty == 0:
            return {}
        
        analytic_dist = {}
        for lot_name, qty in lot_qty_map.items():
            account_id = lot_to_account.get(lot_name)
            if account_id:
                percentage = (qty / total_qty) * 100
                analytic_dist[str(account_id)] = percentage
        
        return analytic_dist

    def _apply_rental_analytic_distribution(self, rental_line, analytic_dist):
        """
        Aplica distribución analítica a línea de alquiler.
        Si no tiene campo analytic_distribution, busca en invoice_line_ids.
        """
        suma = sum(analytic_dist.values())
        
        if abs(suma - 100.0) > 0.1:
            _logger.error(f'Rental line {rental_line.id}: suma={suma:.2f}% != 100%')
            return
        
        # Intentar aplicar en la línea de alquiler
        if hasattr(rental_line, 'analytic_distribution'):
            rental_line.write({'analytic_distribution': analytic_dist})
            _logger.info(f'Distribución aplicada en rental line {rental_line.id}: {analytic_dist}')
        else:
            # Buscar líneas de factura asociadas
            invoice_lines = self.env['account.move.line'].search([
                ('sale_line_ids', 'in', rental_line.sale_order_line_id.ids if hasattr(rental_line, 'sale_order_line_id') else []),
            ])
            
            for invoice_line in invoice_lines:
                invoice_line.write({'analytic_distribution': analytic_dist})
            
            _logger.info(f'Distribución aplicada en {len(invoice_lines)} invoice lines de rental {rental_line.id}')

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

    def _assign_partner_to_rental_accounts(self, account_ids, partner):
        """
        Asigna cliente a cuentas analíticas de alquiler.
        Solo asigna si el campo partner_id está vacío.
        """
        accounts = self.env['account.analytic.account'].browse(list(account_ids))
        
        for account in accounts:
            if not account.partner_id:
                account.write({'partner_id': partner.id})
                _logger.info(f'Cliente {partner.name} asignado a cuenta {account.code} (alquiler pickup)')


class StockPickingRental(models.Model):
    """Hook para detectar pickings de alquiler en validación estándar"""
    _inherit = 'stock.picking'

    def _process_rental_outgoing_picking(self, picking):
        """
        Procesa entregas de alquiler desde button_validate.
        Redirige la lógica a sale.rental si es necesario.
        """
        if not self._is_rental_pickup(picking):
            return
        
        # Buscar orden de alquiler relacionada
        rental_order = self._get_related_rental_order(picking)
        if not rental_order:
            _logger.warning(f'Picking {picking.name} sin orden de alquiler asociada')
            return
        
        # Delegar procesamiento a sale.rental
        rental_order._process_rental_pickup()

    def _process_rental_incoming_picking(self, picking):
        """
        Procesa devoluciones de alquiler desde button_validate.
        Redirige la lógica a sale.rental si es necesario.
        """
        if not self._is_rental_return(picking):
            return
        
        rental_order = self._get_related_rental_order(picking)
        if not rental_order:
            _logger.warning(f'Picking {picking.name} sin orden de alquiler asociada')
            return
        
        # Delegar procesamiento a sale.rental
        rental_order._process_rental_return()

    def _get_related_rental_order(self, picking):
        """Busca la orden de alquiler relacionada con el picking."""
        if picking.origin:
            rental = self.env['sale.rental'].search([
                ('name', '=', picking.origin)
            ], limit=1)
            return rental
        
        return False