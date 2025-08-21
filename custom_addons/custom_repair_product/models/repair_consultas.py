# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class RepairConsulta(models.Model):
    _name = 'repair.consulta'
    _description = 'Consulta técnica'
    
    repair_order_id = fields.Many2one('repair.order', string="Orden de reparación")
    consulta_text = fields.Text(string="Producto a consultar")
    product_uom_qty = fields.Float(string="Cantidad")
    product_uom = fields.Many2one('uom.uom', string="Unidad de medida")
    picked = fields.Boolean(string="Usado")


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('repair_id') or 'repair_line_type' not in vals:
                continue
            repair_id = self.env['repair.order'].browse([vals['repair_id']])
            vals['name'] = repair_id.name
        moves = super().create(vals_list)
        repair_moves = self.env['repair.consulta']
        for move in moves:
            if not move.repair_id:
                continue
            move.group_id = move.repair_id.procurement_group_id.id
            move.origin = move.name
            move.picking_type_id = move.repair_id.picking_type_id.id
            repair_moves |= move
        no_repair_moves = moves - repair_moves
        draft_repair_moves = repair_moves.filtered(lambda m: m.state == 'draft' and m.repair_id.state in ('confirmed', 'under_repair'))
        other_repair_moves = repair_moves - draft_repair_moves
        draft_repair_moves._check_company()
        draft_repair_moves._adjust_procure_method(picking_type_code='repair_operation')
        res = draft_repair_moves._action_confirm()
        res._trigger_scheduler()
        confirmed_repair_moves = (res | other_repair_moves)
        confirmed_repair_moves._create_repair_sale_order_line()
        return (confirmed_repair_moves | no_repair_moves)

    def write(self, vals):
        res = super().write(vals)
        repair_moves = self.env['repair.consulta']
        moves_to_create_so_line = self.env['repair.consulta']
        for move in self:
            if not move.repair_id:
                continue
            # checks vals update
            if not move.sale_line_id and 'sale_line_id' not in vals and move.repair_line_type == 'add':
                moves_to_create_so_line |= move
            if move.sale_line_id and ('repair_line_type' in vals or 'product_uom_qty' in vals):
                repair_moves |= move

        repair_moves._update_repair_sale_order_line()
        moves_to_create_so_line._create_repair_sale_order_line()
        return res

    def _action_cancel(self):
            self._clean_repair_sale_order_line()
            return super()._action_cancel()

    def _clean_repair_sale_order_line(self):
        self.filtered(
            lambda m: m.repair_id and m.sale_line_id
        ).mapped('sale_line_id').write({'product_uom_qty': 0.0})