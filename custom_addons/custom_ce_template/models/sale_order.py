from odoo import models, SUPERUSER_ID, _
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # def action_confirm(self):
    #     res = super().action_confirm()
    #     for order in self:
    #         if order.state == 'sale':
    #             order._send_order_confirmation_mail()
    #     return res

    # def _send_order_confirmation_mail(self):
    #     for order in self:
    #         mail_template = order._get_confirmation_template()
    #         if not mail_template:
    #             _logger.warning("No mail template found for sale order %s", order.name)
    #             return
    #         order._send_order_notification_mail(mail_template)

    def _send_order_notification_mail(self, mail_template):
        self.ensure_one()

        if self.env.su:
            self = self.with_user(SUPERUSER_ID)

        attachments = []

        # Informe estándar del pedido
        try:
            report_action = self.env.ref('sale.action_report_saleorder')
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action.report_name, res_ids=self.ids
            )
            attachment = self.env['ir.attachment'].create({
                'name': f"{self.name}_order.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            attachments.append(attachment.id)
            _logger.info("Generated standard report for %s: %s (ID: %s)", self.name, attachment.name, attachment.id)
        except Exception as e:
            _logger.exception("Failed to render standard sale order report for %s", self.name)
            raise UserError(_("No se pudo generar el PDF del pedido."))

    #     # Informe personalizado "simple"
    #     try:
    #         custom_pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
    #             'custom_ce_template.report_simple_saleorder', res_ids=self.ids
    #         )
    #         custom_attachment = self.env['ir.attachment'].create({
    #             'name': f"Declaración CE - {self.name}.pdf",
    #             'type': 'binary',
    #             'datas': base64.b64encode(custom_pdf_content),
    #             'res_model': self._name,
    #             'res_id': self.id,
    #             'mimetype': 'application/pdf',
    #         })
    #         attachments.append(custom_attachment.id)
    #         _logger.info("Generated simple report for %s: %s (ID: %s)", self.name, custom_attachment.name, custom_attachment.id)
    #     except Exception as e:
    #         _logger.exception("Failed to render custom simple sale order report for %s", self.name)
    #         raise UserError(_("No se pudo generar el informe Declaración CE."))

    #     # Enviar correo
    #     try:
    #         self.with_context(mail_send=True).message_post_with_source(
    #             mail_template,
    #             email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
    #             subtype_xmlid='mail.mt_comment',
    #             attachment_ids=attachments,
    #         )
    #         _logger.info("Sent confirmation email with attachments for sale order %s: %s", self.name, attachments)
    #     except Exception as e:
    #         _logger.exception("Failed to send confirmation email for %s", self.name)
    #         raise UserError(_("No se pudo enviar el correo de confirmación del pedido."))

    # def _get_confirmation_template(self):
    #     self.ensure_one()
    #     param = self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template')
    #     if param:
    #         return self.env['mail.template'].browse(int(param)).exists()
    #     return self.env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)
