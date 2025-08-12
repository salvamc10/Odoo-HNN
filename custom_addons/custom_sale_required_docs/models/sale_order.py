from odoo import api, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _apply_required_docs_from_template(self):
        for order in self:
            if order.template_id:
                order.quotation_document_ids = [
                    (6, 0, order.template_id.required_quotation_document_ids.ids)
                ]
            else:
                order.quotation_document_ids = [(5, 0, 0)]

    @api.onchange('template_id')
    def _onchange_template_id(self):
        res = super()._onchange_template_id()
        self._apply_required_docs_from_template()
        return res

    def write(self, vals):
        template_changed = 'template_id' in vals
        res = super().write(vals)
        if template_changed and not self.env.context.get('install_mode'):
            self._apply_required_docs_from_template()
        return res
