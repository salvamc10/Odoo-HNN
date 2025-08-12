from odoo import api, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _copy_attachment_for_order(self, attachment):
        """Duplica el adjunto en el pedido evitando enlaces cruzados."""
        self.ensure_one()
        # usar copy para preservar metadatos; forzar el binding al pedido
        return attachment.copy({
            'res_model': 'sale.order',
            'res_id': self.id,
        })

    def _attach_template_documents(self, when):
        """when: 'quotation' | 'order'"""
        for order in self:
            template = order.sale_order_template_id
            if not template:
                continue
            docs = template.document_ids
            if when == 'quotation':
                docs = docs.filtered(lambda d: d.attach_on_quotation and d.attachment_id)
            elif when == 'order':
                docs = docs.filtered(lambda d: d.attach_on_order and d.attachment_id)
            if not docs:
                continue
            # Evitar duplicados por nombre+checksum ya adjuntos
            existing = self.env['ir.attachment'].search_read(
                domain=[('res_model', '=', 'sale.order'),
                        ('res_id', '=', order.id)],
                fields=['name', 'checksum']
            )
            existing_keys = {(e['name'], e.get('checksum')) for e in existing}
            for doc in docs:
                att = doc.attachment_id
                key = (att.name, att.checksum)
                if key in existing_keys:
                    continue
                order._copy_attachment_for_order(att)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Adjuntar tras creación del presupuesto
        for rec in records:
            rec._attach_template_documents('quotation')
        return records

    def action_confirm(self):
        res = super().action_confirm()
        # Adjuntar tras confirmar
        for rec in self:
            rec._attach_template_documents('order')
        return res
