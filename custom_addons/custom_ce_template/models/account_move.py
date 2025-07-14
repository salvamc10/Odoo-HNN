from odoo import models, SUPERUSER_ID, _
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_invoice_sent(self):
        """ Opens a wizard to compose an email, with relevant mail template and PDF attachments
        (standard invoice report, Certificado CE from the associated sale order, and product-specific attachments from product_template.invoice_attachment_id) loaded by default """
        self.ensure_one()
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)

        lang = self.env.context.get('lang', self.partner_id.lang or 'es_ES')
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
            _logger.exception("Failed to render standard invoice report for %s", self.name)
            raise UserError(_("No se pudo generar el PDF de la factura: {error}").format(error=str(e)))

        # Add product-specific attachments from product_template.invoice_attachment_id
        try:
            for line in self.invoice_line_ids:
                product_template = line.product_id.product_tmpl_id
                if product_template.invoice_attachment_id and product_template.invoice_attachment_id.id not in attachments:
                    attachments.append(product_template.invoice_attachment_id.id)
                    _logger.info("Added product-specific attachment for product %s: %s", 
                                 product_template.name, product_template.invoice_attachment_id.name)
                else:
                    _logger.debug("No invoice_attachment_id found for product %s in invoice %s", 
                                  product_template.name, self.name)
        except Exception as e:
            _logger.exception("Failed to retrieve product-specific attachments for invoice %s", self.name)
            raise UserError(_("No se pudieron obtener los adjuntos de producto: {error}").format(error=str(e)))

        # Generate Certificado CE for the associated sale order
        try:
            sale_orders = self.line_ids.mapped('sale_line_ids.order_id')
            if not sale_orders and self.invoice_origin:
                sale_orders = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
            for sale_order in sale_orders:
                # Prepare unit_lines with product and lot/serial data
                unit_lines = []
                pickings = self.env['stock.picking'].search([('sale_id', '=', sale_order.id), ('state', '=', 'done')])
                _logger.info("Pickings for sale order %s: %s", sale_order.name, pickings.mapped('name'))
                for line in sale_order.order_line:
                    if not line.display_type and line.product_uom_qty > 0:
                        moves = pickings.mapped('move_ids_without_package').filtered(lambda m: m.sale_line_id == line)
                        _logger.info("Moves for line %s: %s", line.product_id.name, moves.mapped('id'))
                        for move in moves:
                            for lot in move.lot_ids:
                                unit_lines.append({
                                    'index': len(unit_lines) + 1,
                                    'name': line.product_id.name or 'Unnamed Product',
                                    'price_unit': line.price_unit or 0.0,
                                    'price_subtotal': line.price_unit or 0.0,
                                    'default_code': line.product_id.default_code or '',
                                    'lot_name': lot.name or 'N/A',
                                })
                _logger.info("Unit lines for sale order %s: %s", sale_order.name, unit_lines)
                if not unit_lines:
                    _logger.warning("No valid product lines with lot_ids found for sale order %s", sale_order.name)
                
                custom_pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    'custom_ce_template.report_simple_saleorder', res_ids=sale_order.ids, data={'unit_lines': unit_lines}
                )
                custom_attachment = self.env['ir.attachment'].create({
                    'name': f"Certificado CE - {sale_order.name}.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(custom_pdf_content),
                    'res_model': 'sale.order',
                    'res_id': sale_order.id,
                    'mimetype': 'application/pdf',
                })
                attachments.append(custom_attachment.id)
                _logger.info("Generated Certificado CE for sale order %s: %s", sale_order.name, custom_attachment.name)
        except Exception as e:
            _logger.exception("Failed to generate Certificado CE for invoice %s, sale order %s",
                              self.name, sale_order.name)
            raise UserError(_("No se pudo generar el Certificado CE: {error}").format(error=str(e)))

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
        else:
            _logger.warning("No mail template found for invoice %s", self.name)

        if attachments:
            ctx['default_attachment_ids'] = [(6, 0, attachments)]
            _logger.info("Context for mail.compose.message for invoice %s: %s", self.name, ctx)
        else:
            _logger.warning("No attachments found for invoice %s", self.name)

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
        """ Get the appropriate mail template for the current invoice. """
        self.ensure_one()
        # Verifica el identificador correcto de la plantilla de correo en tu base de datos
        return self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)

    def _send_invoice_notification_mail(self, mail_template):
        """ Send a mail to the customer with PDF attachments: the standard invoice report,
        the Certificado CE from the associated sale order, and product-specific attachments. """
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
            _logger.info("Generated standard invoice report for %s: %s (ID: %s)", self.name, attachment.name, attachment.id)
        except Exception as e:
            _logger.exception("Failed to render standard invoice report for %s", self.name)
            raise UserError(_("No se pudo generar el PDF de la factura: {error}").format(error=str(e)))

        # Add product-specific attachments
        try:
            for line in self.invoice_line_ids:
                product_template = line.product_id.product_tmpl_id
                if product_template.invoice_attachment_id and product_template.invoice_attachment_id.id not in attachments:
                    attachments.append(product_template.invoice_attachment_id.id)
                    _logger.info("Added product-specific attachment for product %s: %s (ID: %s)",
                                 product_template.name, product_template.invoice_attachment_id.name, 
                                 product_template.invoice_attachment_id.id)
        except Exception as e:
            _logger.exception("Failed to retrieve product-specific attachments for invoice %s", self.name)
            raise UserError(_("No se pudieron obtener los adjuntos de producto: {error}").format(error=str(e)))

        # Generate Certificado CE for the associated sale order
        try:
            sale_orders = self.line_ids.mapped('sale_line_ids.order_id')
            for sale_order in sale_orders:
                # Prepare unit_lines with product and lot/serial data
                unit_lines = []
                pickings = self.env['stock.picking'].search([('sale_id', '=', sale_order.id), ('state', '=', 'done')])
                _logger.info("Pickings for sale order %s: %s", sale_order.name, pickings.mapped('name'))
                for line in sale_order.order_line:
                    if not line.display_type and line.product_uom_qty > 0:
                        moves = pickings.mapped('move_ids_without_package').filtered(lambda m: m.sale_line_id == line)
                        _logger.info("Moves for line %s: %s", line.product_id.name, moves.mapped('id'))
                        for move in moves:
                            for lot in move.lot_ids:
                                unit_lines.append({
                                    'index': len(unit_lines) + 1,
                                    'name': line.product_id.name or 'Unnamed Product',
                                    'price_unit': line.price_unit or 0.0,
                                    'price_subtotal': line.price_unit or 0.0,
                                    'default_code': line.product_id.default_code or '',
                                    'lot_name': lot.name or 'N/A',
                                })
                _logger.info("Unit lines for sale order %s: %s", sale_order.name, unit_lines)
                if not unit_lines:
                    _logger.warning("No valid product lines with lot_ids found for sale order %s", sale_order.name)
                
                custom_pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    'custom_ce_template.report_simple_saleorder', res_ids=sale_order.ids, data={'unit_lines': unit_lines}
                )
                custom_attachment = self.env['ir.attachment'].create({
                    'name': f"Certificado CE - {sale_order.name}.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(custom_pdf_content),
                    'res_model': 'sale.order',
                    'res_id': sale_order.id,
                    'mimetype': 'application/pdf',
                })
                attachments.append(custom_attachment.id)
                _logger.info("Generated Certificado CE for sale order %s: %s (ID: %s)",
                             sale_order.name, custom_attachment.name, custom_attachment.id)
        except Exception as e:
            _logger.exception("Failed to generate Certificado CE for invoice %s, sale order %s",
                              self.name, sale_order.name)
            raise UserError(_("No se pudo generar el Certificado CE: {error}").format(error=str(e)))

        try:
            self.with_context(mail_send=True).message_post_with_source(
                mail_template,
                email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                subtype_xmlid='mail.mt_comment',
                attachment_ids=attachments,
            )
            _logger.info("Sent invoice email with attachments for invoice %s: %s", self.name, attachments)
        except Exception as e:
            _logger.exception("Failed to send invoice email for %s", self.name)
            raise UserError(_("No se pudo enviar el correo con la factura: {error}").format(error=str(e)))