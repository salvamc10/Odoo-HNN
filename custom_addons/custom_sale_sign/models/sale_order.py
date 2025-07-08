from odoo import models, api, fields
from odoo.tools import pdf
import base64

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sign_request_ids = fields.Many2many('sign.request', string='Signature Requests', copy=False)

    def action_quotation_send(self):
        """Sobreescribe el método de envío de presupuesto para crear un registro en el módulo de Firmas."""
        res = super(SaleOrder, self).action_quotation_send()

        # Obtener la plantilla de firma (reemplaza con el ID real de tu plantilla)
        sign_template = self.env['sign.template'].browse([10])  # Cambia ID_DE_LA_PLANTILLA por el ID real

        for order in self:
            # Generar el PDF del presupuesto
            report = self.env.ref('sale.action_report_saleorder')
            pdf_content, _ = report._render_qweb_pdf([order.id])

            # Crear un adjunto para el PDF
            attachment = self.env['ir.attachment'].create({
                'name': f'{order.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'sale.order',
                'res_id': order.id,
            })

            # Crear un registro en el módulo de Firmas
            sign_request = self.env['sign.request'].create({
                'template_id': sign_template.id,
                'reference': f'Firma para {order.name}',
                'subject': f'Por favor, firme el presupuesto {order.name}',
                'partner_ids': [(6, 0, [order.partner_id.id])],
                'attachment_ids': [(6, 0, [attachment.id])],
                'reference_doc': f'sale.order,{order.id}',
                'state': 'sent',
            })

            # Crear el elemento de firma para el cliente
            sign_request_item = self.env['sign.request.item'].create({
                'sign_request_id': sign_request.id,
                'partner_id': order.partner_id.id,
                'role_id': self.env.ref('sign.sign_item_role_signer').id,  # Rol de firmante
                'signer_email': order.partner_id.email,
            })

            # Enviar el enlace de firma al cliente
            sign_request.with_context(force_send=False).send_signature_accesses()

            # Vincular el sign.request al pedido de venta
            order.write({'sign_request_ids': [(4, sign_request.id)]})

        return res