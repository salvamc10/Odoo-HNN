from collections import defaultdict
from odoo import models, fields # type: ignore

class LotLabelLayout(models.TransientModel):
    _inherit = "lot.label.layout"

    print_format = fields.Selection(
        selection_add=[('dymo', 'Dymo')],
        ondelete={'dymo': 'set default'}
    )

    def _get_report_name(self):
        if self.print_format == 'dymo':
            return 'custom_label_dymo.report_lotlabel_dymo'
        return super()._get_report_name()
