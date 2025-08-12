from odoo import api, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _load_default_quotation_documents(self):
        for order in self:
            if not order.template_id:
                order.quotation_document_ids = [(5, 0, 0)]
                continue
            required_docs = order.template_id.custom_template_doc_ids.filtered("required").mapped("document_id")
            order.quotation_document_ids = [(6, 0, required_docs.ids)]

    @api.onchange("template_id")
    def _onchange_template_id_docs_defaults(self):
        res = super()._onchange_template_id()
        self._load_default_quotation_documents()
        return res

    def write(self, vals):
        template_changed = "template_id" in vals
        res = super().write(vals)
        if template_changed:
            self._load_default_quotation_documents()
        return res
