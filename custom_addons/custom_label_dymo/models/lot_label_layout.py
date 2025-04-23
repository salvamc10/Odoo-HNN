from collections import defaultdict
from odoo import models, fields # type: ignore


class LotLabelLayout(models.TransientModel):
    _inherit = 'lot.label.layout'

    print_format = fields.Selection(
        selection_add=[('dymo', 'Dymo')],
        ondelete={'dymo': 'set default'}
    )

    def process(self):
        self.ensure_one()
        if self.print_format == 'zpl':
            xml_id = 'stock.label_lot_template'
        elif self.print_format == 'dymo':
            xml_id = 'custom_label_dymo.action_report_lotlabel_dymo'
        else:
            xml_id = 'stock.action_report_lot_label'

        if self.label_quantity == 'lots':
            docids = self.move_line_ids.lot_id.ids
        else:
            uom_categ_unit = self.env.ref('uom.product_uom_categ_unit')
            quantity_by_lot = defaultdict(int)
            for move_line in self.move_line_ids:
                if not move_line.lot_id:
                    continue
                if move_line.product_uom_id.category_id == uom_categ_unit:
                    quantity_by_lot[move_line.lot_id.id] += int(move_line.quantity)
                else:
                    quantity_by_lot[move_line.lot_id.id] += 1
            docids = []
            for lot_id, qty in quantity_by_lot.items():
                docids.extend([lot_id] * qty)

        report_action = self.env.ref(xml_id).report_action(docids, config=False)
        report_action.update({'close_on_report_download': True})
        return report_action
