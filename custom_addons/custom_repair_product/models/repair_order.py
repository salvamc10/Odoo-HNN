from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    @api.onchange('lot_id')
    def _onchange_lot_id_set_product(self):
        for ro in self:
            if not ro.lot_id:
                continue
            lot = ro.lot_id
            if lot.product_id:
                ro.product_id = lot.product_id
                if hasattr(ro, 'product_uom') and ro.product_id.uom_id:
                    ro.product_uom = ro.product_id.uom_id
            if hasattr(ro, 'product_qty'):
                ro.product_qty = 1.0

    @api.onchange('product_id')
    def _onchange_product_id_adjust_lot(self):
        for ro in self:
            if not ro.product_id:
                continue
            warning = None
            if ro.lot_id and ro.lot_id.product_id and ro.lot_id.product_id != ro.product_id:
                ro.lot_id = False
                warning = {
                    'title': _('Lote incoherente'),
                    'message': _('El lote/serie seleccionado pertenece a otro producto. Se deseleccionará.'),
                }
            tracking = ro.product_id.tracking
            if tracking == 'serial' and hasattr(ro, 'product_qty'):
                ro.product_qty = 1.0
            if tracking not in ('lot', 'serial') and ro.lot_id:
                ro.lot_id = False
                warning = warning or {
                    'title': _('Producto no trazable'),
                    'message': _('El producto no usa lotes/series, se ha eliminado el lote/serie.'),
                }
            if warning:
                return {'warning': warning}

    @api.constrains('product_id', 'lot_id')
    def _check_product_lot_consistency(self):
        for ro in self:
            if ro.lot_id and ro.product_id and ro.lot_id.product_id and ro.lot_id.product_id != ro.product_id:
                raise ValidationError(_('El lote/serie no corresponde con el producto seleccionado.'))
