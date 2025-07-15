from odoo import models, SUPERUSER_ID
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """ Override action_confirm to generate PDF reports """
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.state == 'sale':
                try:
                    # Generar el informe estándar
                    report_action = self.env.ref('sale.action_report_saleorder')
                    pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                        report_action.report_name, res_ids=order.ids
                    )
                    attachment = self.env['ir.attachment'].create({
                        'name': f"{order.name}_order.pdf",
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': order._name,
                        'res_id': order.id,
                        'mimetype': 'application/pdf',
                    })
                    _logger.info("Generated standard report for %s: %s (ID: %s)", order.name, attachment.name, attachment.id)
                    self.env.cr.commit()

                    # Generar el informe personalizado solo si hay lot_ids
                    unit_lines = []
                    pickings = self.env['stock.picking'].search([('sale_id', '=', order.id), ('state', '=', 'done')])
                    _logger.info("Pickings for %s: %s", order.name, pickings.mapped('name'))
                    if not pickings:
                        _logger.warning("No done pickings found for %s", order.name)
                    for line in order.order_line:
                        if not line.display_type and line.product_uom_qty > 0:
                            _logger.info("Processing line %s (product: %s, tracking: %s, sale_line_id: %s)", 
                                         line.id, line.product_id.name, line.product_id.tracking, line.id)
                            moves = pickings.mapped('move_ids').filtered(lambda m: m.sale_line_id.id == line.id)
                            _logger.info("Moves for line %s (product: %s): %s", 
                                         line.id, line.product_id.name, moves.mapped('id'))
                            if not moves:
                                _logger.info("No moves found for line %s (product: %s)", 
                                             line.id, line.product_id.name)
                            for move in moves:
                                _logger.info("Move %s: product=%s, sale_line_id=%s, lot_ids=%s", 
                                             move.id, move.product_id.name, move.sale_line_id.id, move.lot_ids.mapped('name'))
                                if move.lot_ids:
                                    for lot in move.lot_ids:
                                        unit_lines.append({
                                            'index': len(unit_lines) + 1,
                                            'name': line.product_id.name or 'Unnamed Product',
                                            'price_unit': line.price_unit or 0.0,
                                            'price_subtotal': line.price_subtotal or 0.0,
                                            'default_code': line.product_id.default_code or '',
                                            'lot_name': lot.name,
                                        })
                                else:
                                    _logger.info("No lot_ids found for move %s (product: %s)", 
                                                 move.id, line.product_id.name)
                    _logger.info("Unit lines for %s: %s", order.name, unit_lines)

                    if unit_lines:  # Solo generar el certificado si hay unit_lines
                        context = self.env.context.copy()
                        context.update({
                            'unit_lines': unit_lines,
                            'lang': order.partner_id.lang or 'es_ES',
                        })
                        custom_pdf_content, _ = self.env['ir.actions.report'].with_context(**context)._render_qweb_pdf(
                            'custom_ce_template.report_simple_saleorder', res_ids=order.ids
                        )
                        custom_attachment = self.env['ir.attachment'].create({
                            'name': f"Certificado CE - {order.name}.pdf",
                            'type': 'binary',
                            'datas': base64.b64encode(custom_pdf_content),
                            'res_model': order._name,
                            'res_id': order.id,
                            'mimetype': 'application/pdf',
                        })
                        _logger.info("Generated custom CE report for %s: %s (ID: %s)", 
                                     order.name, custom_attachment.name, custom_attachment.id)
                        self.env.cr.commit()
                    else:
                        _logger.warning("No custom CE report generated for %s: No valid unit lines found", order.name)
                except Exception as e:
                    _logger.error("Failed to generate reports for %s: %s", order.name, str(e))
                    raise
                order._send_order_notification_mail(order._get_confirmation_template())
        return res

    def _send_order_notification_mail(self, mail_template):
        """ Send a mail to the customer without attachments """
        self.ensure_one()

        if not mail_template:
            _logger.warning("No mail template provided for sale order %s", self.name)
            return

        if self.env.su:
            self = self.with_user(SUPERUSER_ID)

        try:
            self.with_context(mail_send=True).message_post_with_source(
                mail_template,
                email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                subtype_xmlid='mail.mt_comment',
                attachment_ids=[],
            )
            _logger.info("Sent confirmation email without attachments for sale order %s", self.name)
        except Exception as e:
            _logger.error("Failed to send confirmation email for %s: %s", self.name, str(e))

    def action_quotation_send(self):
        """ Opens a wizard to compose an email without attachments """
        self.filtered(lambda so: so.state in ('draft', 'sent')).order_line._validate_analytic_distribution()
        lang = self.env.context.get('lang')
        self.ensure_one()

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
        """ Get the appropriate mail template for the current sales order based on its state """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state != 'sale':
            return self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        else:
            return self._get_confirmation_template()

    def _get_confirmation_template(self):
        """ Get the mail template sent on SO confirmation """
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

    def action_quotation_sent(self):
        """ Mark the given draft quotation(s) as sent """
        if any(order.state != 'draft' for order in self):
            raise UserError(_("Only draft orders can be marked as sent directly."))

        for order in self:
            order.message_subscribe(partner_ids=order.partner_id.ids)

        self.write({'state': 'sent'})

    def action_invoice_create(self, grouped=False, final=False, date=None):
        """ Prevent duplicate invoices """
        self.ensure_one()
        existing_invoices = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('state', '!=', 'cancel'),
        ])
        if existing_invoices:
            _logger.warning("Invoice already exists for sale order %s: %s", self.name, existing_invoices.mapped('name'))
            return existing_invoices.ids
        _logger.info("No existing invoices found for sale order %s (ID: %s). Creating new invoice.", self.name, self.id)
        return super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final, date=date)