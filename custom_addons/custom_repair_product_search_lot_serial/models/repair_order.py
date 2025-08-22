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
        domain="[('id', 'in', allowed_lot_ids), '|', ('name', 'ilike', x_machine_number), ('x_machine_number', 'ilike', x_machine_number)]",
        check_company=True, help="Products repaired are all belonging to this lot")

    x_machine_number = fields.Many2one(
        'stock.lot', string='Machine Number',
        domain="[('id', 'in', allowed_lot_ids)]", check_company=True,
        help="Machine number to search or create a lot/serial")

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
                domain = [('product_id.type', '=', 'consu'), '|', ('product_id.company_id', '=', False), ('product_id.company_id', '=', self.company_id.id)]
            repair.allowed_lot_ids = self.env['stock.lot'].search(domain) or self.env['stock.lot']

    @api.onchange('x_machine_number')
    def _onchange_x_machine_number(self):
        if self.x_machine_number:
            self.lot_id = self.x_machine_number
        else:
            self.lot_id = False

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.x_machine_number = self.lot_id
        else:
            self.x_machine_number = False