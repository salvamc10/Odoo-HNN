from odoo import api, fields, models
from odoo.osv import expression

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

    x_machine_number = fields.Many2one(
        'stock.lot', string='Machine Number',
        domain="[('id', 'in', allowed_lot_ids)]", check_company=True,
        help="Machine number to search or create a lot/serial",
        context={'show_x_machine_number': True})  # Pasar contexto para personalizar la visualización

    # Campo computed necesario para el dominio
    allowed_lot_ids = fields.Many2many(
        'stock.lot', compute='_compute_allowed_lot_ids', 
        string='Allowed Lot IDs')

    @api.depends('lot_id', 'lot_id.product_id', 'x_machine_number', 'x_machine_number.product_id')
    def _compute_product_id(self):
        for repair in self:
            if repair.lot_id:
                repair.product_id = repair.lot_id.product_id
            elif repair.x_machine_number:
                repair.product_id = repair.x_machine_number.product_id
            else:
                repair.product_id = False

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

    @api.onchange('x_machine_number')
    def _onchange_x_machine_number(self):
        if self.x_machine_number:
            self.lot_id = self.x_machine_number
            self.product_id = self.x_machine_number.product_id
        else:
            self.lot_id = False
            self.product_id = False

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.product_id = self.lot_id.product_id
            if self.lot_id.x_machine_number:
                # Buscar un lote diferente con el mismo número de máquina
                machine_lots = self.env['stock.lot'].search([
                    ('x_machine_number', '=', self.lot_id.x_machine_number),
                    ('product_id', '=', self.lot_id.product_id.id),
                    ('id', '!=', self.lot_id.id)
                ], limit=1)
                self.x_machine_number = machine_lots if machine_lots else False
            else:
                self.x_machine_number = False
        else:
            self.x_machine_number = False
            self.product_id = False

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