from odoo import models, fields

class LotLabelLayout(models.TransientModel):
    _inherit = "lot.label.layout"

    def _get_print_format_selection(self):
        res = super()._get_print_format_selection()
        res.append(('dymo', 'Dymo'))
        return res

    def _get_report_name(self):
        if self.print_format == 'dymo':
            return 'product.report_producttemplatelabel_dymo'
        return super()._get_report_name()
