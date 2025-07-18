from odoo import models, api, SUPERUSER_ID
import base64
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

   
    def action_invoice_sent(self):
        self.ensure_one()
        lang = self.env.context.get('lang', self.partner_id.lang or 'es_ES')
        mail_template = self._find_invoice_mail_template()
        attachments = []
    
        # PDF estándar de la factura
        try:
            report_action = self.env.ref('account.account_invoices')
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action.report_name, res_ids=[self.id]
            )
            invoice_attachment = self.env['ir.attachment'].create({
                'name': f"{self.name}_invoice.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            attachments.append(invoice_attachment.id)
        except Exception as e:
            _logger.error("Error generando PDF de factura %s: %s", self.name, str(e))
    
        # Certificado CE (ya copiado a account.move)
        ce_attach = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id),
            ('name', 'ilike', 'Certificado CE%'),
            ('mimetype', '=', 'application/pdf'),
        ], limit=1)
        if ce_attach:
            attachments.append(ce_attach.id)
    
        # Archivos desde product.template (invoice_attachment_id)
        for line in self.invoice_line_ids:
            attach = line.product_id.product_tmpl_id.invoice_attachment_id
            if attach and attach.id not in attachments:
                attachments.append(attach.id)
    
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
    
        if attachments:
            ctx['default_attachment_ids'] = [(6, 0, attachments)]
    
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }
    
    def _send_invoice_notification_mail(self, mail_template):
        self.ensure_one()
    
        if not mail_template:
            _logger.warning("No mail template provided for invoice %s", self.name)
            return
    
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)
    
        attachments = []
    
        # PDF estándar
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
        except Exception as e:
            _logger.error("Error generando PDF factura %s: %s", self.name, str(e))
    
        # CE
        ce_attach = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id),
            ('name', 'ilike', 'Certificado CE%'),
            ('mimetype', '=', 'application/pdf'),
        ], limit=1)
        if ce_attach:
            attachments.append(ce_attach.id)
    
        # Archivos desde invoice_attachment_id
        for line in self.invoice_line_ids:
            attach = line.product_id.product_tmpl_id.invoice_attachment_id
            if attach and attach.id not in attachments:
                attachments.append(attach.id)
    
        try:
            message = self.with_context(
                mail_send=True,
                default_attachment_ids=[(6, 0, attachments)]
            ).message_post_with_source(
                mail_template,
                email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                subtype_xmlid='mail.mt_comment',
                attachment_ids=attachments,
            )
            _logger.info("Enviado correo factura %s, mensaje ID: %s", self.name, message.id)
        except Exception as e:
            _logger.error("Error enviando correo factura %s: %s", self.name, str(e))

    def _find_invoice_mail_template(self):
        self.ensure_one()
        return self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.invoice_origin:
                order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
                if order:
                    cert = self.env['ir.attachment'].search([
                        ('res_model', '=', 'sale.order'),
                        ('res_id', '=', order.id),
                        ('name', 'ilike', 'Certificado CE'),
                    ], limit=1)
                    if cert:
                        cert.copy({
                            'res_model': 'account.move',
                            'res_id': move.id,
                        })
                        _logger.info("Adjuntado certificado CE a la factura %s desde pedido %s", move.name, order.name)
        return moves

    def action_post(self):
        res = super().action_post()
        for invoice in self:
            if invoice.move_type != 'out_invoice':
                continue

            attachments = []

            try:
                report_action = self.env.ref('account.account_invoices')
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    report_action.report_name, res_ids=invoice.ids
                )
                attach = self.env['ir.attachment'].create({
                    'name': f"{invoice.name}_invoice.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'mimetype': 'application/pdf',
                })
                attachments.append(attach.id)
                _logger.info("Adjuntado PDF a factura %s", invoice.name)
            except Exception as e:
                _logger.error("Error generando PDF %s: %s", invoice.name, str(e))

            for line in invoice.invoice_line_ids:
                tmpl = line.product_id.product_tmpl_id
                attach = tmpl.invoice_attachment_id
                if attach and attach.id not in attachments:
                    attachments.append(attach.id)
                    _logger.info("Adjuntado manual %s para producto %s", attach.name, tmpl.name)

            sale_orders = invoice.invoice_line_ids.mapped('sale_line_ids.order_id')
            for order in sale_orders:
                pickings = self.env['stock.picking'].search([
                    ('sale_id', '=', order.id),
                    ('state', '=', 'done')
                ])
                unit_lines = []
                for line in order.order_line:
                    if line.product_id.type == 'service' and not line.display_type and line.price_subtotal:
                        continue
                    else:
                        moves = pickings.mapped('move_ids').filtered(lambda m: m.sale_line_id.id == line.id)
                        for move in moves:
                            for lot in move.lot_ids:
                                unit_lines.append({
                                    'index': len(unit_lines) + 1,
                                    'name': line.product_id.name,
                                    'price_unit': line.price_unit,
                                    'price_subtotal': line.price_subtotal,
                                    'default_code': line.product_id.default_code,
                                    'lot_name': lot.name,
                                })

                if unit_lines:
                    context = self.env.context.copy()
                    context.update({
                        'unit_lines': unit_lines,
                        'lang': invoice.partner_id.lang or 'es_ES',
                    })
                    try:
                        ce_pdf, _ = self.env['ir.actions.report'].with_context(**context)._render_qweb_pdf(
                            'custom_ce_template.report_simple_saleorder',
                            res_ids=order.ids
                        )
                        ce_attach = self.env['ir.attachment'].create({
                            'name': f"Certificado CE - {order.name}.pdf",
                            'type': 'binary',
                            'datas': base64.b64encode(ce_pdf),
                            'res_model': 'account.move',
                            'res_id': invoice.id,
                            'mimetype': 'application/pdf',
                        })
                        attachments.append(ce_attach.id)
                        _logger.info("Adjuntado certificado CE a %s", invoice.name)
                    except Exception as e:
                        _logger.error("Error generando CE para %s: %s", invoice.name, str(e))

            if attachments:
                invoice.message_post(
                    body="Documentos adjuntos generados automáticamente.",
                    attachment_ids=attachments
                )
        return res
