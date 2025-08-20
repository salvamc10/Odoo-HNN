from odoo import api, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _apply_required_docs_from_template(self):
        for order in self:
            tmpl = order.sale_order_template_id
            order.quotation_document_ids = (
                [(6, 0, tmpl.required_quotation_document_ids.ids)] if tmpl else [(5, 0, 0)]
            )

    @api.onchange('sale_order_template_id')
    def _onchange_sale_order_template_id(self):
        parent = getattr(super(), '_onchange_sale_order_template_id', None)
        res = parent() if parent else {}
        self._apply_required_docs_from_template()
        return res

    @api.model
    def _add_missing_default_values(self, values):
        values = super()._add_missing_default_values(values)
        if not values.get('name'):
            company_id = values.get('company_id') or self.env.company.id
            values['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('sale.order') or 'New'
        return values
