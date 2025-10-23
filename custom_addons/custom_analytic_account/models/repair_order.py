from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Cuenta Analítica del Producto',
        compute='_compute_analytic_account_id',
        store=True,
        readonly=True,
        help='Cuenta analítica asociada al lote/serie del producto a reparar'
    )

    @api.depends('lot_id', 'lot_id.name')
    def _compute_analytic_account_id(self):
        """
        Busca la cuenta analítica asociada al lote/serie del producto a reparar.
        """
        for repair in self:
            if repair.lot_id:
                account = self.env['account.analytic.account'].search([
                    ('code', '=', repair.lot_id.name),
                ], limit=1)
                repair.analytic_account_id = account.id if account else False
            else:
                repair.analytic_account_id = False

    def action_repair_confirm(self):
        """
        Override: Al confirmar la reparación, asigna distribución analítica a todas las líneas.
        """
        res = super(RepairOrder, self).action_repair_confirm()
        
        for repair in self:
            repair._assign_analytic_to_repair_lines()
        
        return res

    def action_repair_invoice_create(self):
        """
        Override: Al crear la factura, asegura que las líneas tengan distribución analítica.
        """
        res = super(RepairOrder, self).action_repair_invoice_create()
        
        for repair in self:
            repair._assign_analytic_to_repair_lines()
            # También asignar a líneas de factura si se crearon
            if repair.invoice_id:
                repair._assign_analytic_to_invoice_lines()
        
        return res

    def _assign_analytic_to_repair_lines(self):
        """
        Asigna el 100% de distribución analítica a todas las líneas de operaciones
        basándose en la cuenta analítica del producto a reparar.
        """
        self.ensure_one()
        
        if not self.analytic_account_id:
            _logger.warning(
                f"Reparación {self.name}: No se encontró cuenta analítica para el lote/serie {self.lot_id.name if self.lot_id else 'N/A'}"
            )
            return
        
        # Distribución: 100% a la cuenta analítica del producto reparado
        analytic_dist = {self.analytic_account_id.id: 100.0}
        
        # Aplicar a todas las líneas de operaciones (piezas/componentes)
        lines_updated = 0
        for operation in self.operations:
            if operation.type in ('add', 'remove'):  # Solo líneas de productos
                operation.write({'analytic_distribution': analytic_dist})
                lines_updated += 1
        
        # Aplicar a líneas de honorarios/mano de obra
        for fee in self.fees_lines:
            fee.write({'analytic_distribution': analytic_dist})
            lines_updated += 1
        
        _logger.info(
            f"Reparación {self.name}: {lines_updated} líneas actualizadas con distribución analítica {analytic_dist}"
        )

    def _assign_analytic_to_invoice_lines(self):
        """
        Asigna distribución analítica a las líneas de factura generadas.
        """
        self.ensure_one()
        
        if not self.invoice_id or not self.analytic_account_id:
            return
        
        analytic_dist = {self.analytic_account_id.id: 100.0}
        
        for invoice_line in self.invoice_id.invoice_line_ids:
            # Solo actualizar líneas relacionadas con esta reparación
            if invoice_line.name and self.name in invoice_line.name:
                invoice_line.write({'analytic_distribution': analytic_dist})
        
        _logger.info(
            f"Reparación {self.name}: Distribución analítica aplicada a factura {self.invoice_id.name}"
        )

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """
        Al cambiar el lote/serie, recalcula la cuenta analítica.
        """
        # El compute se encarga, pero podemos mostrar un warning si no existe
        if self.lot_id:
            account = self.env['account.analytic.account'].search([
                ('code', '=', self.lot_id.name),
            ], limit=1)
            if not account:
                return {
                    'warning': {
                        'title': _('Cuenta Analítica No Encontrada'),
                        'message': _(
                            f'No existe cuenta analítica para el lote/serie {self.lot_id.name}. '
                            'La distribución analítica no se aplicará.'
                        )
                    }
                }