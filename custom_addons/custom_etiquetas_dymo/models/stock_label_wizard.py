from odoo import models, fields # type: ignore

class StockLabelWizard(models.TransientModel):
    _inherit = 'stock.label.wizard'

    format = fields.Selection(selection_add=[
        ('54x25', '54 x 25')
    ])

    def action_print_labels(self):
        self.ensure_one()
        if self.format == '54x25':
            return self.env.ref('custom_etiquetas_dymo_54x25.action_report_label_54x25').report_action(self._get_target_lots())
        return super().action_print_labels()
