from odoo import models, api, SUPERUSER_ID
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _generate_unit_lines(self):
        """ Generar unit_lines para el informe simple """
        unit_lines = []
        _logger.info("Order lines for %s: %s", self.name, [(line.name, line.product_uom_qty, line.price_unit, line.display_type, line.product_id.default_code) for line in self.order_line])
        for line in self.order_line:
            if not line.display_type and line.product_uom_qty > 0 and line.name and line.product_id.default_code:
                qty = int(line.product_uom_qty)
                for i in range(qty):
                    unit_lines.append({
                        'index': i + 1,
                        'name': line.name.strip(),
                        'price_unit': line.price_unit or 0.0,
                        'price_subtotal': line.price_unit or 0.0,
                        'default_code': line.product_id.default_code.strip(),
                    })
        _logger.info("Unit lines for %s: %s", self.name, unit_lines)
        if not unit_lines:
            _logger.warning("No valid unit lines generated for %s", self.name)
        return unit_lines

    def _send_order_confirmation_mail(self):
        """ Send a mail to the SO customer to inform them that their order has been confirmed. """
        for order in self:
            mail_template = order._get_confirmation_template()
            if mail_template:
                order._send_order_notification_mail(mail_template)
            else:
                _logger.warning("No mail template found for sale order %s", order.name)

    def _send_order_notification_mail(self, mail_template):
        """ Send a mail to the customer with two PDF attachments: the standard sale order report
        and one custom simple report containing one page per product unit. """
        self.ensure_one()

        if not mail_template:
            _logger.warning("No mail template provided for sale order %s", self.name)
            return

        if self.env.su:
            self = self.with_user(SUPERUSER_ID)

        attachments = []
        try:
            # Render the standard sale order report
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
            _logger.info("Generated standard report for %s: %s", self.name, attachment.name)
        except Exception as e:
            _logger.error("Failed to render standard sale order report for %s: %s", self.name, str(e))

        # Generate one PDF with one page per product unit
        try:
            custom_report_action = self.env.ref('custom_ce_template.action_report_simple_saleorder')
            unit_lines = self._generate_unit_lines()
            if unit_lines:
                lang = 'es_ES'
                self = self.with_context(unit_lines=unit_lines, lang=lang)
                _logger.info("Context for rendering simple report for %s: %s", self.name, {'unit_lines': unit_lines, 'lang': lang})
                custom_pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    custom_report_action.report_name, res_ids=self.ids
                )
                custom_attachment = self.env['ir.attachment'].create({
                    'name': f"{self.name}_simple_order.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(custom_pdf_content),
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                })
                attachments.append(custom_attachment.id)
                _logger.info("Generated simple report for %s: %s", self.name, custom_attachment.name)
            else:
                _logger.warning("No unit lines generated for %s: no valid order lines found", self.name)
        except Exception as e:
            _logger.error("Failed to render custom simple sale order report for %s: %s", self.name, str(e))


        if attachments:
            try:
                self.with_context(mail_send=True).message_post_with_source(
                    mail_template,
                    email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                    subtype_xmlid='mail.mt_comment',
                    attachment_ids=attachments,
                )
                _logger.info("Sent confirmation email with attachments for sale order %s: %s", self.name, attachments)
            except Exception as e:
                _logger.error("Failed to send confirmation email for %s: %s", self.name, str(e))
        else:
            _logger.warning("No attachments generated for sale order %s", self.name)

    def action_quotation_send(self):
        """ Opens a wizard to compose an email, with relevant mail template and two PDF attachments. """
        self.filtered(lambda so: so.state in ('draft', 'sent')).order_line._validate_analytic_distribution()
        lang = 'es_ES'
        self.ensure_one()

        attachments = []
        try:
            # Render the standard sale order report
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
            _logger.info("Generated standard report for %s: %s", self.name, attachment.name)
        except Exception as e:
            _logger.error("Failed to render standard sale order report for %s: %s", self.name, str(e))

        # Generate one PDF with one page per product unit
        try:
            custom_report_action = self.env.ref('custom_ce_template.action_report_simple_saleorder')
            unit_lines = self._generate_unit_lines()
            if unit_lines:
                self = self.with_context(unit_lines=unit_lines, lang=lang)
                _logger.info("Context for rendering simple report for %s: %s", self.name, {'unit_lines': unit_lines, 'lang': lang})
                custom_pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    custom_report_action.report_name, res_ids=self.ids
                )
                custom_attachment = self.env['ir.attachment'].create({
                    'name': f"{self.name}_simple_order.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(custom_pdf_content),
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                })
                attachments.append(custom_attachment.id)
                _logger.info("Generated simple report for %s: %s", self.name, custom_attachment.name)
            else:
                _logger.warning("No unit lines generated for %s: no valid order lines found", self.name)
        except Exception as e:
            _logger.error("Failed to render custom simple sale order report for %s: %s", self.name, str(e))

        ctx = {
            'default_model': 'sale.order',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'email_notification_allow_footer': True,
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }

        if not self.env.context.get('hide_default_template'):
            mail_template = self._find_mail_template()
            if mail_template:
                ctx.update({
                    'default_template_id': mail_template.id,
                    'mark_so_as_sent': True,
                })
                if mail_template and mail_template.lang:
                    lang = mail_template._render_lang(self.ids)[self.id]
        else:
            self._portal_ensure_token()

        if attachments:
            ctx['default_attachment_ids'] = [(6, 0, attachments)]
            _logger.info("Context for mail.compose.message: %s", ctx)

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

        if (
            self.env.context.get('check_document_layout')
            and not self.env.context.get('discard_logo_check')
            and self.env.is_admin()
            and not self.env.company.external_report_layout_id
        ):
            layout_action = self.env['ir.actions.report']._action_configure_external_report_layout(
                action,
            )
            action.pop('close_on_report_download', None)
            layout_action['context']['dialog_size'] = 'extra-large'
            return layout_action
        return action

    def _find_mail_template(self):
        """ Get the appropriate mail template for the current sales order based on its state. """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state != 'sale':
            return self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        else:
            return self._get_confirmation_template()

    def _get_confirmation_template(self):
        """ Get the mail template sent on SO confirmation (or for confirmed SO's). """
        self.ensure_one()
        default_confirmation_template_id = self.env['ir.config_parameter'].sudo().get_param(
            'sale.default_confirmation_template'
        )
        default_confirmation_template = default_confirmation_template_id \
            and self.env['mail.template'].browse(int(default_confirmation_template_id)).exists()
        if default_confirmation_template:
            return default_confirmation_template
        else:
            return self.env.ref('sale.mail_template_sale_confirmation', raise_if_not_found=False)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_data(self, res_ids):
        """ Sobrescribir para añadir unit_lines al contexto para el informe simple """
        data = super()._render_qweb_pdf_prepare_data(res_ids)
        _logger.info("Rendering report %s for res_ids: %s", self.report_name, res_ids)
        if self.report_name == 'custom_ce_template.report_simple_saleorder':
            records = self.env['sale.order'].browse(res_ids)
            unit_lines = []
            for order in records:
                _logger.info("Preparing unit_lines for report %s, order %s", self.report_name, order.name)
                unit_lines.extend(order._generate_unit_lines())
            if unit_lines:
                data['context'] = data.get('context', {})
                data['context'].update({
                    'unit_lines': unit_lines,
                    'lang': 'es_ES',
                })
                _logger.info("Updated context with unit_lines for report %s: %s", self.report_name, data['context'])
            else:
                _logger.warning("No unit lines generated for report %s", self.report_name)
        return data