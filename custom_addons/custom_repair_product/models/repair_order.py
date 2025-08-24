from odoo import api, fields, models, _ # type: ignore
from odoo.exceptions import ValidationError # type: ignore

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    machine_lot_id = fields.Many2one(
        'stock.lot',
        string='Número de máquina',
        domain="[('x_machine_number', '!=', False), ('company_id', '=', company_id)]",
        context="{'lot_display': 'machine'}",
        copy=False,
    )

    @api.onchange('machine_lot_id')
    def _onchange_machine_lot_id(self):
        for ro in self:
            lot = ro.machine_lot_id
            if not lot:
                return

            ro.lot_id = lot

            product = lot.product_id
            if product:
                ro.product_id = product
                if hasattr(ro, 'product_uom') and product.uom_id:
                    ro.product_uom = product.uom_id
                if product.tracking == 'serial':
                    ro.product_qty = 1.0

    @api.onchange('lot_id')
    def _onchange_lot_sync_machine(self):
        for ro in self:
            lot = ro.lot_id
            if not lot:
                ro.machine_lot_id = False
                return

            ro.machine_lot_id = lot if lot.x_machine_number else False

            product = lot.product_id
            if product:
                ro.product_id = product
                if hasattr(ro, 'product_uom') and product.uom_id:
                    ro.product_uom = product.uom_id
                if product.tracking == 'serial':
                    ro.product_qty = 1.0

    @api.constrains('product_id', 'lot_id', 'machine_lot_id')
    def _check_consistency(self):
        for ro in self:
            if ro.machine_lot_id and ro.lot_id and ro.machine_lot_id != ro.lot_id:
                raise ValidationError(_('El Nº de máquina y el lote/serie deben referir al mismo lote.'))
            if ro.lot_id and ro.product_id and ro.lot_id.product_id and ro.lot_id.product_id != ro.product_id:
                raise ValidationError(_('El lote/serie no corresponde con el producto.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('machine_lot_id') and not vals.get('lot_id'):
                vals['lot_id'] = vals['machine_lot_id']
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            if vals.get('machine_lot_id') and not vals.get('lot_id'):
                vals['lot_id'] = vals['machine_lot_id']
        return super().write(vals)
