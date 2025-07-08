from odoo import models, api, fields
from odoo.tools import pdf
import base64
from odoo.http import request

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sign_request_ids = fields.Many2many('sign.request', string='Signature Requests', copy=False)
    sign_request_url = fields.Char(
        string='Signature URL',
        compute='_compute_sign_request_url',
        help='URL to access the signature request for this sale order.'
    )

    def _compute_sign_request_url(self):
        """Calcula la URL del sign.request más reciente asociado al pedido."""
        for order in self:
            sign_request = order.sign_request_ids[:1]  # Toma el primer sign.request
            if sign_request and sign_request.request_item_ids:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                sign_request_item = sign_request.request_item_ids[0]
                order.sign_request_url = f"{base_url}/sign/document/mail/{sign_request.id}/{sign_request_item.access_token}"
            else:
                order.sign_request_url = False

    def action_quotation_send(self):
        """Sobreescribe el método de envío de presupuesto para crear un registro en el módulo de Firmas."""
        # Generar el sign.request antes de enviar el correo
        for order in self:
            # Obtener la plantilla de firma (reemplaza con el ID real de tu plantilla)
            sign_template = self.env['sign.template'].browse([ID_DE_LA_PLANTILLA])  # Cambia ID_DE_LA_PLANTILLA por el ID real

            # Verificar si ya existe un sign.request para evitar duplicados
            if not order.sign_request_ids.filtered(lambda sr: sr.state == 'sent'):
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
                self.env['sign.request.item'].create({
                    'sign_request_id': sign_request.id,
                    'partner_id': order.partner_id.id,
                    'role_id': self.env.ref('sign.sign_item_role_signer').id,
                    'signer_email': order.partner_id.email,
                })

                # Vincular el sign.request al pedido de venta
                order.write({'sign_request_ids': [(4, sign_request.id)]})

        # Enviar el correo con el PDF (que incluirá la URL)
        res = super(SaleOrder, self).action_quotation_send()

        # Enviar el enlace de firma al cliente
        for order in self:
            sign_request = order.sign_request_ids[:1]
            if sign_request:
                sign_request.with_context(force_send=False).send_signature_accesses()

        return res