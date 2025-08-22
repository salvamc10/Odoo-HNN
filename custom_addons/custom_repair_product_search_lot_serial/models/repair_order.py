from odoo import fields, models, api

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    product_id = fields.Many2one(
        'product.product', string='Product to Repair',
        domain="[('type', '=', 'consu'), '|', ('company_id', '=', company_id), ('company_id', '=', False), '|', ('id', 'in', picking_product_ids), ('id', '=?', picking_product_id)]",
        compute='_compute_product_id', store=True, readonly=True,  # Product_id es calculado y de solo lectura, derivado de lot_id
        check_company=True)

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial',
        domain="[('id', 'in', allowed_lot_ids)]", check_company=True,
        help="Products repaired are all belonging to this lot")  # Lot_id es entrada manual, sin compute

    x_machine_number = fields.Char(
        string='Machine Number',
        related='lot_id.x_machine_number', readonly=True,
        help="Machine number associated with the selected lot/serial")
    
    @api.depends('lot_id', 'lot_id.product_id')
    def _compute_product_id(self):
        for repair in self:
            repair.product_id = repair.lot_id.product_id if repair.lot_id else False

    @api.depends('product_id', 'company_id', 'picking_id', 'picking_id.move_ids', 'picking_id.move_ids.lot_ids')
    def _compute_allowed_lot_ids(self):
        for repair in self:
            domain = []
            if repair.product_id:
                domain.append(('product_id', '=', repair.product_id.id))
            if repair.picking_id:
                picking_lot_domain = [('id', 'in', repair.picking_id.move_ids.lot_ids.ids or [])]
                if domain:
                    domain = expression.AND([domain, picking_lot_domain])
                else:
                    domain = picking_lot_domain
            if not domain:
                # Permitimos buscar cualquier lote de productos consumibles en la compañía
                domain = [('product_id.type', '=', 'consu'), '|', ('product_id.company_id', '=', False), ('product_id.company_id', '=', repair.company_id.id)]
            repair.allowed_lot_ids = self.env['stock.lot'].search(domain) or self.env['stock.lot']
            
    @api.onchange('x_machine_number')
    def _onchange_x_machine_number(self):
        if self.x_machine_number:
            # Buscar lotes que coincidan con x_machine_number o name
            lots = self.env['stock.lot'].search([
                '|', ('x_machine_number', 'ilike', self.x_machine_number), ('name', 'ilike', self.x_machine_number),
                ('product_id.type', '=', 'consu'),
                '|', ('product_id.company_id', '=', False), ('product_id.company_id', '=', self.company_id.id)
            ], limit=1)
            if lots:
                self.lot_id = lots[0]
            else:
                # Si no se encuentra un lote, preparamos el contexto para crear uno nuevo con x_machine_number
                self.lot_id = False
                return {
                    'context': dict(self.env.context, default_x_machine_number=self.x_machine_number)
                }
            
class StockLot(models.Model):
    _inherit = 'stock.lot'

    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('x_machine_number', operator, name)]
        try:
            lots = self.search(domain + args, limit=limit)
            return lots.name_get() if lots else []
        except Exception as e:
            # Log del error para depuración (opcional)
            _logger.error(f"Error in name_search for stock.lot: {e}")
            return []