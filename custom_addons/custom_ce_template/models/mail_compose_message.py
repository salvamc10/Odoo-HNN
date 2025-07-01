from odoo import models, api

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res.get('model') == 'sale.order' and res.get('res_id'):
            order = self.env['sale.order'].browse(res['res_id'])
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'sale.order'),
                ('res_id', '=', order.id)
            ])
            res['attachment_ids'] = [(6, 0, attachments.ids)]
        return res