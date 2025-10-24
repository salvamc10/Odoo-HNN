from odoo import api, fields, models, _
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

    def action_create_sale_order(self):
        """
        Override: Al crear el presupuesto, asigna distribución analítica a todas las líneas.
        """
        res = super(RepairOrder, self).action_create_sale_order()
        
        for repair in self:
            if repair.sale_order_id and repair.analytic_account_id:
                repair._assign_analytic_to_sale_order_lines()
            elif not repair.analytic_account_id:
                _logger.warning(
                    f"Reparación {repair.name}: No se encontró cuenta analítica para el lote/serie "
                    f"{repair.lot_id.name if repair.lot_id else 'N/A'}"
                )
        
        return res

    def _assign_analytic_to_sale_order_lines(self):
        """
        Asigna el 100% de distribución analítica a todas las líneas del pedido de venta
        basándose en la cuenta analítica del producto a reparar.
        """
        self.ensure_one()
        
        if not self.sale_order_id or not self.analytic_account_id:
            return
        
        # Distribución: 100% a la cuenta analítica del producto reparado
        analytic_dist = {str(self.analytic_account_id.id): 100.0}
        
        lines_updated = 0
        for sale_line in self.sale_order_id.order_line:
            sale_line.write({'analytic_distribution': analytic_dist})
            lines_updated += 1        
        
    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """
        Al cambiar el lote/serie, muestra warning si no existe cuenta analítica.
        """
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