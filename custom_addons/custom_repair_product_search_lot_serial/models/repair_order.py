from odoo import api, fields, models
from odoo.osv import expression
import logging

_logger = logging.getLogger(__name__)

class Repair(models.Model):
    _inherit = 'repair.order'

    product_id = fields.Many2one(
        'product.product', string='Product to Repair',
        domain="[('type', '=', 'consu'), '|', ('company_id', '=', company_id), ('company_id', '=', False), '|', ('id', 'in', picking_product_ids), ('id', '=?', picking_product_id)]",
        compute='_compute_product_id', store=True, readonly=True,
        check_company=True)

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial',
        domain="[('id', 'in', allowed_lot_ids)]", check_company=True,
        help="Products repaired are all belonging to this lot")

    x_machine_number = fields.Char(
        string='Machine Number',
        compute='_compute_x_machine_number', store=True, readonly=True,
        help="Machine number associated with the lot")

    # Campo computed necesario para el dominio
    allowed_lot_ids = fields.Many2many(
        'stock.lot', compute='_compute_allowed_lot_ids', 
        string='Allowed Lot IDs')

    @api.depends('lot_id', 'lot_id.product_id', 'lot_id.x_machine_number')
    def _compute_product_id(self):
        for repair in self:
            if repair.lot_id:
                repair.product_id = repair.lot_id.product_id
            else:
                repair.product_id = False

    @api.depends('lot_id', 'lot_id.x_machine_number')
    def _compute_x_machine_number(self):
        for repair in self:
            machine_number = repair.lot_id.x_machine_number if repair.lot_id else False
            _logger.info("Computing x_machine_number for repair %s: lot_id=%s, x_machine_number=%s", 
                         repair.id, repair.lot_id.name if repair.lot_id else None, machine_number)
            repair.x_machine_number = machine_number

    @api.depends('product_id', 'company_id', 'picking_id', 'picking_id.move_ids', 'picking_id.move_ids.lot_ids')
    def _compute_allowed_lot_ids(self):
        for repair in self:
            domain = []
            if repair.product_id:
                domain.append(('product_id', '=', repair.product_id.id))
            if repair.picking_id:
                picking_lot_domain = [('id', 'in', repair.picking_id.move_ids.lot_ids.ids or [])]
                if domain:
                    domain = expression.AND([domain, picking_lot_domain]) if domain else picking_lot_domain                
            if not domain:
                domain = [('product_id.type', '=', 'consu'), 
                         '|', ('product_id.company_id', '=', False), 
                         ('product_id.company_id', '=', repair.company_id.id if repair.company_id else False)]
            
            lots = self.env['stock.lot'].search(domain)
            repair.allowed_lot_ids = [(6, 0, lots.ids)]

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.product_id = self.lot_id.product_id
            self.x_machine_number = self.lot_id.x_machine_number
        else:
            self.product_id = False
            self.x_machine_number = False

    def clear_selection(self):
        """Método para limpiar la selección y permitir nueva búsqueda"""
        self.product_id = False
        self.lot_id = False
        self.x_machine_number = False


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def name_get(self):
        result = []
        for lot in self:
            if self.env.context.get('show_x_machine_number') and lot.x_machine_number:
                name = lot.x_machine_number
            elif self.env.context.get('show_lot_name') and lot.name:
                name = f"{lot.x_machine_number or 'No Machine'} (Serial: {lot.name})"
            else:
                name = lot.name
            result.append((lot.id, name))
        return result
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if name:
            domain = ['|', ('name', operator, name), ('x_machine_number', operator, name)]
            lots = self.search(domain + args, limit=limit)
            return lots.name_get()
        return super(StockLot, self).name_search(name=name, args=args, operator=operator, limit=limit)