from odoo import api, models, _
import logging

_logger = logging.getLogger(__name__)

class RentalOrderWizard(models.TransientModel):
    """Interceptar validación del wizard de alquiler"""
    _inherit = 'rental.order.wizard'
    
    def apply(self):
        _logger.info('========== WIZARD APPLY EJECUTADO ==========')
        res = super().apply()
        _logger.info(f'========== RESULTADO SUPER: {res} ==========')
        
        picking = self._get_validated_picking()
        _logger.info(f'========== PICKING ENCONTRADO: {picking} ==========')
        
        if picking:
            _logger.info(f'[WIZARD] Procesando picking {picking.name} desde wizard')
            
            # Determinar si es entrega o devolución
            if self.status == 'pickup':
                self._process_rental_outgoing(picking)
            elif self.status == 'return':
                self._process_rental_incoming(picking)
        
        return res
    
    def _get_validated_picking(self):
        """Obtener el picking recién validado"""
        # El wizard tiene acceso al pedido
        order = self.order_id
        
        if not order or not hasattr(order, 'is_rental') or not order.is_rental:
            return False
        
        # Buscar el último picking validado del pedido
        picking = self.env['stock.picking'].search([
            ('origin', '=', order.name),
            ('state', '=', 'done')
        ], order='date_done desc', limit=1)
        
        return picking
    
    def _process_rental_outgoing(self, picking):
        """Procesa entregas de alquiler"""
        rental_order = picking.sale_id
        
        if not rental_order or not picking.move_line_ids:
            return
        
        distribution_data = self._group_qty_by_sale_line_and_lot(picking.move_line_ids)
        
        for sale_line_id, lot_qty_map in distribution_data.items():
            sale_line = self.env['sale.order.line'].browse(sale_line_id)
            lot_to_account = self._get_analytic_accounts_by_lot_names(lot_qty_map.keys())
            
            if not lot_to_account:
                continue
            
            analytic_dist = self._calculate_analytic_distribution(
                lot_qty_map, lot_to_account, order_line=sale_line
            )
            
            if analytic_dist:
                self._apply_analytic_distribution(sale_line, analytic_dist, 'rental')
                self._assign_partner_to_analytic_accounts(
                    lot_to_account.values(), rental_order.partner_id, is_rental=True
                )
                _logger.info(f'✓ Distribución aplicada a {sale_line.display_name}')
    
    def _process_rental_incoming(self, picking):
        """Procesa devoluciones"""
        rental_order = picking.sale_id
        
        if not rental_order or not picking.move_line_ids:
            return
        
        lot_names = self._get_unique_lot_names(picking.move_line_ids)
        
        for lot_name in lot_names:
            account = self.env['account.analytic.account'].search([
                ('code', '=', lot_name)
            ], limit=1)
            
            if account and account.partner_id:
                account.write({'partner_id': False})
                _logger.info(f'✓ Cliente limpiado de cuenta {lot_name}')
    
    # Métodos auxiliares (copiar de tu modelo stock.picking)
    def _group_qty_by_sale_line_and_lot(self, move_lines):
        """Agrupa cantidades por línea de venta y lote"""
        result = {}
        for ml in move_lines:
            if not ml.sale_line_id or not ml.lot_id:
                continue
            
            sale_line_id = ml.sale_line_id.id
            lot_name = ml.lot_id.name
            
            if sale_line_id not in result:
                result[sale_line_id] = {}
            
            result[sale_line_id][lot_name] = result[sale_line_id].get(lot_name, 0) + ml.quantity
        
        return result
    
    def _get_unique_lot_names(self, move_lines):
        """Extrae nombres únicos de lotes"""
        return list(set(ml.lot_id.name for ml in move_lines if ml.lot_id))
    
    def _get_analytic_accounts_by_lot_names(self, lot_names):
        """Mapea lotes a cuentas analíticas"""
        accounts = self.env['account.analytic.account'].search([
            ('code', 'in', list(lot_names))
        ])
        return {acc.code: acc for acc in accounts}
    
    def _calculate_analytic_distribution(self, lot_qty_map, lot_to_account, order_line=None):
        """Calcula distribución proporcional"""
        total_qty = sum(lot_qty_map.values())
        if total_qty == 0:
            return {}
        
        distribution = {}
        for lot_name, qty in lot_qty_map.items():
            account = lot_to_account.get(lot_name)
            if account:
                percentage = round((qty / total_qty) * 100, 2)
                distribution[str(account.id)] = percentage
        
        return distribution
    
    def _apply_analytic_distribution(self, sale_line, distribution, source):
        """Aplica distribución a la línea de venta"""
        sale_line.write({'analytic_distribution': distribution})
    
    def _assign_partner_to_analytic_accounts(self, accounts, partner, is_rental=False):
        """Asigna cliente a cuentas analíticas"""
        for account in accounts:
            if not account.partner_id:
                account.write({'partner_id': partner.id})