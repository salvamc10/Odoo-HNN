from odoo import models, api, SUPERUSER_ID
import base64
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_invoice_sent(self):
        """ Opens a wizard to compose an email, with relevant mail template and PDF attachments
        (standard invoice report, custom simple report from the associated sale order, and product-specific attachments from product_template.invoice_attachment_id) loaded by default """
        self.ensure_one()
        lang = self.env.context.get('lang')
        mail_template = self._find_invoice_mail_template()

        attachments = []
        # Generate the standard invoice report
        try:
            report_action = self.env.ref('account.account_invoices')
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action.report_name, res_ids=self.ids
            )
            attachment = self.env['ir.attachment'].create({
                'name': f"{self.name}_invoice.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            attachments.append(attachment.id)
            _logger.info("Generated standard invoice report for %s: %s", self.name, attachment.name)
        except Exception as e:
            _logger.error("Failed to render standard invoice report for %s: %s", self.name, str(e))

        # Add product-specific attachments from product_template.invoice_attachment_id
        try:
            for line in self.invoice_line_ids:
                product_template = line.product_id.product_tmpl_id
                if product_template.invoice_attachment_id:
                    if product_template.invoice_attachment_id.id not in attachments:
                        attachments.append(product_template.invoice_attachment_id.id)
                        _logger.info("Added product-specific attachment for product %s: %s", 
                                     product_template.name, product_template.invoice_attachment_id.name)
                else:
                    _logger.debug("No invoice_attachment_id found for product %s in invoice %s", 
                                  product_template.name, self.name)
        except Exception as e:
            _logger.error("Failed to retrieve product-specific attachments for invoice %s: %s", self.name, str(e))

        # Find the custom simple report from the associated sale order
        try:
            sale_orders = self.line_ids.mapped('sale_line_ids.order_id')
            if sale_orders:
                for sale_order in sale_orders:
                    custom_attachment = self.env['ir.attachment'].search([
                        ('res_model', '=', 'sale.order'),
                        ('res_id', '=', sale_order.id),
                        ('name', '=', f"{sale_order.name}_simple_order.pdf"),
                        ('mimetype', '=', 'application/pdf'),
                    ], limit=1)
                    if custom_attachment:
                        if custom_attachment.id not in attachments:
                            attachments.append(custom_attachment.id)
                            _logger.info("Found custom simple report for sale order %s: %s", 
                                         sale_order.name, custom_attachment.name)
                    else:
                        _logger.warning("No custom simple report found for sale order %s", sale_order.name)
            else:
                _logger.warning("No sale orders found for invoice %s", self.name)
        except Exception as e:
            _logger.error("Failed to retrieve custom simple report for invoice %s: %s", self.name, str(e))

        ctx = {
            'default_model': 'account.move',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'email_notification_allow_footer': True,
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }

        if mail_template:
            ctx.update({
                'default_template_id': mail_template.id,
                'mark_invoice_as_sent': True,
            })
            if mail_template.lang:
                lang = mail_template._render_lang(self.ids)[self.id]
        else:
            _logger.warning("No mail template found for invoice %s", self.name)

        if attachments:
            ctx['default_attachment_ids'] = [(6, 0, attachments)]
            _logger.info("Context for mail.compose.message for invoice %s: %s", self.name, ctx)
        else:
            _logger.warning("No attachments found for invoice %s, proceeding with email wizard without attachments", self.name)

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _find_invoice_mail_template(self):
        """ Get the appropriate mail template for the current invoice.

        :return: The correct mail template for the invoice
        :rtype: record of `mail.template` or `None` if not found
        """
        self.ensure_one()
        return self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)

    def _send_invoice_notification_mail(self, mail_template):
        """ Send a mail to the customer with PDF attachments: the standard invoice report,
        the custom simple report from the associated sale order, and product-specific attachments from product_template.invoice_attachment_id.

        Note: self.ensure_one()

        :param mail.template mail_template: the template used to generate the mail
        :return: None
        """
        self.ensure_one()

        if not mail_template:
            _logger.warning("No mail template provided for invoice %s", self.name)
            return

        if self.env.su:
            self = self.with_user(SUPERUSER_ID)

        attachments = []
        # Generate the standard invoice report
        try:
            report_action = self.env.ref('account.account_invoices')
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action.report_name, res_ids=self.ids
            )
            attachment = self.env['ir.attachment'].create({
                'name': f"{self.name}_invoice.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            attachments.append(attachment.id)
            _logger.info("Generated standard invoice report for %s: %s", self.name, attachment.name)
        except Exception as e:
            _logger.error("Failed to render standard invoice report for %s: %s", self.name, str(e))

        # Add product-specific attachments from product_template.invoice_attachment_id
        try:
            for line in self.invoice_line_ids:
                product_template = line.product_id.product_tmpl_id
                if product_template.invoice_attachment_id:
                    if product_template.invoice_attachment_id.id not in attachments:
                        attachments.append(product_template.invoice_attachment_id.id)
                        _logger.info("Added product-specific attachment for product %s: %s", 
                                     product_template.name, product_template.invoice_attachment_id.name)
                else:
                    _logger.debug("No invoice_attachment_id found for product %s in invoice %s", 
                                  product_template.name, self.name)
        except Exception as e:
            _logger.error("Failed to retrieve product-specific attachments for invoice %s: %s", self.name, str(e))

        # Find the custom simple report from the associated sale order
        try:
            sale_orders = self.line_ids.mapped('sale_line_ids.order_id')
            if sale_orders:
                for sale_order in sale_orders:
                    custom_attachment = self.env['ir.attachment'].search([
                        ('res_model', '=', 'sale.order'),
                        ('res_id', '=', sale_order.id),
                        ('name', '=', f"{sale_order.name}_simple_order.pdf"),
                        ('mimetype', '=', 'application/pdf'),
                    ], limit=1)
                    if custom_attachment:
                        if custom_attachment.id not in attachments:
                            attachments.append(custom_attachment.id)
                            _logger.info("Found custom simple report for sale order %s: %s", 
                                         sale_order.name, custom_attachment.name)
                    else:
                        _logger.warning("No custom simple report found for sale order %s", sale_order.name)
            else:
                _logger.warning("No sale orders found for invoice %s", self.name)
        except Exception as e:
            _logger.error("Failed to retrieve custom simple report for invoice %s: %s", self.name, str(e))

        if attachments:
            try:
                self.with_context(mail_send=True).message_post_with_source(
                    mail_template,
                    email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                    subtype_xmlid='mail.mt_comment',
                    attachment_ids=attachments,
                )
                _logger.info("Sent invoice email with attachments for invoice %s: %s", self.name, attachments)
            except Exception as e:
                _logger.error("Failed to send invoice email for %s: %s", self.name, str(e))
        else:
            _logger.warning("No attachments generated for invoice %s, sending email without attachments", self.name)
            try:
                self.with_context(mail_send=True).message_post_with_source(
                    mail_template,
                    email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                    subtype_xmlid='mail.mt_comment',
                    attachment_ids=[],
                )
                _logger.info("Sent invoice email without attachments for invoice %s", self.name)
            except Exception as e:
                _logger.error("Failed to send invoice email without attachments for %s: %s", self.name, str(e))