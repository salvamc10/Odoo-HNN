from collections import defaultdict
from odoo import models, fields # type: ignore

class LotLabelLayout(models.TransientModel):
    _inherit = "lot.label.layout"

    print_format = fields.Selection([
        ('4x12', '4 x 12'),
        ('zpl', 'ZPL Labels'),
        ('dymo', 'Dymo')], string="Format", default='4x12', required=True)

    def _get_report_name(self):
        if self.print_format == 'dymo':
            return 'product.report_producttemplatelabel_dymo'
        return super()._get_report_name()
