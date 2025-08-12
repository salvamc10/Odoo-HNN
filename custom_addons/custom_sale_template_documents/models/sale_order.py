from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _attach_template_documents(self, when):
        for order in self:
            template = order.sale_order_template_id
            if not template:
                continue
            docs = template.custom_auto_document_ids.filtered(
                lambda d: (d.attach_on_quotation if when == 'quotation' else d.attach_on_order)
            )
            existing = self.env['ir.attachment'].search_read([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id),
            ], ['name', 'checksum'])
            existing_keys = {(e['name'], e.get('checksum')) for e in existing}
            for doc in docs:
                att = doc.document_id.attachment_id
                if not att:
                    continue
                key = (att.name, att.checksum)
                if key in existing_keys:
                    continue
                att.copy({
                    'res_model': 'sale.order',
                    'res_id': order.id,
                })

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._attach_template_documents('quotation')
        return records

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._attach_template_documents('order')
        return res
