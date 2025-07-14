from odoo import models, SUPERUSER_ID
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     for order in self:
    #         if order.state == 'sale':
    #             order._send_order_confirmation_mail()
    #     return res

    # def _send_order_confirmation_mail(self):
    #     """ Send a mail to the SO customer to inform them that their order has been confirmed.
    #     :return: None
    #     """
    #     for order in self:
    #         mail_template = order._get_confirmation_template()
    #         if mail_template:
    #             order._send_order_notification_mail(mail_template)
    #         else:
    #             _logger.warning("No mail template found for sale order %s", order.name)

    def _send_order_notification_mail(self, mail_template):
        """ Send a mail to the customer with two PDF attachments: the standard sale order report
        and one custom simple report containing one page per product unit with lot_ids.

        Note: self.ensure_one()

        :param mail.template mail_template: the template used to generate the mail
        :return: None
        """
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
            _logger.info("Generated standard report for %s: %s (ID: %s)", self.name, attachment.name, attachment.id)
            self.env.cr.commit()
        except Exception as e:
            _logger.error("Failed to render standard sale order report for %s: %s", self.name, str(e))

        # Generate one PDF with one page per product unit
        try:
            # Usar directamente la plantilla QWeb
            custom_pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                'custom_ce_template.report_simple_saleorder', res_ids=self.ids
            )
            custom_attachment = self.env['ir.attachment'].create({
                'name': f"Declaración CE - {self.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(custom_pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            attachments.append(custom_attachment.id)
            _logger.info("Generated simple report for %s: %s (ID: %s)", self.name, custom_attachment.name, custom_attachment.id)
            self.env.cr.commit()
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
        """ Opens a wizard to compose an email, with relevant mail template and two PDF attachments
        (standard report and one simple report with one page per product unit with lot_ids) loaded by default """
        self.filtered(lambda so: so.state in ('draft', 'sent')).order_line._validate_analytic_distribution()
        lang = self.env.context.get('lang')
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

        # Generate one PDF with one page per product unit with lot_ids
        try:
            custom_report_action = self.env.ref('custom_ce_template.action_report_simple_saleorder')
            unit_lines = []
            # Obtener las entregas asociadas al pedido de venta
            pickings = self.env['stock.picking'].search([('sale_id', '=', self.id), ('state', '=', 'done')])
            _logger.info("Pickings for %s: %s", self.name, pickings.mapped('name'))
            
            for line in self.order_line:
                if not line.display_type and line.product_uom_qty > 0:  # Excluir líneas de tipo display y con cantidad 0
                    # Obtener movimientos de inventario asociados a la línea
                    moves = pickings.mapped('move_ids_without_package').filtered(lambda m: m.sale_line_id == line)
                    _logger.info("Moves for line %s: %s", line.product_id.name, moves.mapped('id'))
                    for move in moves:
                        for lot in move.lot_ids:
                            # Solo incluir productos con lot_ids
                            unit_lines.append({
                                'index': len(unit_lines) + 1,
                                'name': line.product_id.name or 'Unnamed Product',
                                'price_unit': line.price_unit or 0.0,
                                'price_subtotal': line.price_unit or 0.0,
                                'default_code': line.product_id.default_code or '',
                                'lot_name': lot.name,  # Número de serie
                            })
            _logger.info("Unit lines for %s: %s", self.name, unit_lines)

            if unit_lines:
                context = self.env.context.copy()
                context.update({
                    'unit_lines': unit_lines,
                    'lang': self.partner_id.lang or 'es_ES',
                })
                self = self.with_context(**context)
                _logger.info("Context for rendering simple report for %s: %s", self.name, context)
                custom_pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    custom_report_action.report_name, res_ids=self.ids
                )
                custom_attachment = self.env['ir.attachment'].create({
                    'name': f"{self.name}_certificado_CE.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(custom_pdf_content),
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                })
                attachments.append(custom_attachment.id)
                _logger.info("Generated simple report for %s: %s", self.name, custom_attachment.name)
            else:
                _logger.warning("No unit lines generated for %s: no valid order lines with lot_ids found", self.name)
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
        """ Get the appropriate mail template for the current sales order based on its state.

        If the SO is confirmed, we return the mail template for the sale confirmation.
        Otherwise, we return the quotation email template.

        :return: The correct mail template based on the current status
        :rtype: record of `mail.template` or `None` if not found
        """
        self.ensure_one()
        if self.env.context.get('proforma') or self.state != 'sale':
            return self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        else:
            return self._get_confirmation_template()

    def _get_confirmation_template(self):
        """ Get the mail template sent on SO confirmation (or for confirmed SO's).

        :return: `mail.template` record or None if default template wasn't found
        """
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
        """ Mark the given draft quotation(s) as sent.

        :raise: UserError if any given SO is not in draft state.
        """
        if any(order.state != 'draft' for order in self):
            raise UserError(_("Only draft orders can be marked as sent directly."))

        for order in self:
            order.message_subscribe(partner_ids=order.partner_id.ids)

        self.write({'state': 'sent'})
        

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_data(self, res_ids):
        """ Sobrescribir para mantener compatibilidad, pero no generar unit_lines aquí """
        return super()._render_qweb_pdf_prepare_data(res_ids)