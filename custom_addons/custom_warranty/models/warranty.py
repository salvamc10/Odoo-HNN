from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    warranty_period = fields.Selection([
        ('3', '3 meses'),
        ('6', '6 meses'),
        ('12', '12 meses'),
        ('18', '18 meses'),
        ('24', '24 meses'),
        ('36', '36 meses'),
    ],
        string='Periodo de garantía',
        help='Meses de duración de la garantía para productos con número de serie.',
    )

class StockLot(models.Model):
    _inherit = 'stock.lot'

    WARRANTY_SELECTION = [
        ('3', '3 meses'),
        ('6', '6 meses'),
        ('12', '12 meses'),
        ('18', '18 meses'),
        ('24', '24 meses'),
        ('36', '36 meses'),
    ]

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de venta origen',
        help='Pedido de venta asociado a este lote.'
    )
    warranty_start_date = fields.Date(
        string='Inicio de garantía',
        help='Fecha desde la que comienza la garantía. Se asigna automáticamente con la fecha de factura.',
        readonly=True
    )
    warranty_months = fields.Selection(
        WARRANTY_SELECTION,
        string='Duración garantía (meses)',
        help='Número de meses de duración de la garantía asignada a este producto.'
    )
    warranty_expiration_date = fields.Date(
        string='Garantía hasta',
        compute='_compute_warranty_expiration_date',
        store=True,
        help='Fecha de vencimiento de la garantía calculada automáticamente.'
    )

    @api.depends('warranty_start_date', 'warranty_months')
    def _compute_warranty_expiration_date(self):
        for lot in self:
            if lot.warranty_start_date and lot.warranty_months:
                lot.warranty_expiration_date = lot.warranty_start_date + relativedelta(months=int(lot.warranty_months))
            else:
                lot.warranty_expiration_date = False

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        res = super()._post(soft)
        for move in self:
            if move.move_type != 'out_invoice':
                continue
            for line in move.invoice_line_ids:
                sale_order = line.sale_line_ids.order_id if line.sale_line_ids else False
                if sale_order and sale_order.warranty_period:
                    for sale_line in line.sale_line_ids:
                        for move in sale_line.move_ids:
                            for move_line in move.move_line_ids:
                                if move_line.lot_id and move_line.product_id.tracking == 'serial':
                                    lot = move_line.lot_id
                                    lot.sale_order_id = sale_order
                                    lot.warranty_months = sale_order.warranty_period
                                    lot.warranty_start_date = self.invoice_date
        return res
