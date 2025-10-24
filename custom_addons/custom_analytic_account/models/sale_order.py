from odoo import api, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Lógica de distribución analítica para ALQUILERES"""
    _inherit = 'sale.order'

    def action_open_pickup(self):
        """Hook para pickings de alquiler - delegar a stock.picking"""
        return super().action_open_pickup()

    def action_open_return(self):
        """Hook para devoluciones - delegar a stock.picking"""
        return super().action_open_return()


class StockPickingRental(models.Model):
    """Procesamiento de pickings de alquiler"""
    _inherit = 'stock.picking'

    def _process_rental_outgoing_picking(self, picking):
        """Procesa entregas de alquiler: asigna distribución y cliente"""
        rental_order = self._get_related_rental_order(picking)
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

    def _process_rental_incoming_picking(self, picking):
        """Procesa devoluciones: limpia cliente de cuentas"""
        rental_order = self._get_related_rental_order(picking)
        if not rental_order or not picking.move_line_ids:
            return
        
        lot_names = self._get_unique_lot_names(picking.move_line_ids)
        
        for lot_name in lot_names:
            account = self.env['account.analytic.account'].search([('code', '=', lot_name)], limit=1)
            if account and account.partner_id:
                account.write({'partner_id': False})
                _logger.info(f'Cliente limpiado cuenta {lot_name} (devolución {rental_order.name})')

    def _get_related_rental_order(self, picking):
        """Busca orden de alquiler por origin o sale_id.is_rental"""
        if picking.sale_id and hasattr(picking.sale_id, 'is_rental') and picking.sale_id.is_rental:
            return picking.sale_id
        
        if picking.origin:
            rental = self.env['sale.order'].search([
                ('name', '=', picking.origin),
                ('is_rental', '=', True)
            ], limit=1)
            return rental
        
        return False