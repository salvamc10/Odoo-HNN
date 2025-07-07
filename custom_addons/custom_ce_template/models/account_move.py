from odoo import models, api, SUPERUSER_ID
import base64
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_invoice_sent(self):
        """ Opens a wizard to compose an email, with relevant mail template and two PDF attachments
        (standard invoice report and one custom simple report with one page per product unit with lot_ids) loaded by default """
        self.ensure_one()
        lang = self.env.context.get('lang')
        mail_template = self._find_invoice_mail_template()

        attachments = []
        try:
            # Render the standard invoice report
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

        # Generate one PDF with one page per product unit with lot_ids
        try:
            custom_report_action = self.env.ref('custom_ce_template.action_report_simple_saleorder')
            unit_lines = []
            # Obtener el pedido de venta asociado a la factura
            sale_orders = self.line_ids.mapped('sale_line_ids.order_id')
            if sale_orders:
                # Obtener las entregas asociadas al pedido de venta
                pickings = self.env['stock.picking'].search([('sale_id', 'in', sale_orders.ids), ('state', '=', 'done')])
                _logger.info("Pickings for invoice %s: %s", self.name, pickings.mapped('name'))

                for line in self.line_ids:
                    if not line.display_type and line.quantity > 0:  # Excluir líneas de tipo display y con cantidad 0
                        # Obtener movimientos de inventario asociados a la línea de la factura
                        sale_lines = line.sale_line_ids
                        moves = pickings.mapped('move_ids_without_package').filtered(lambda m: m.sale_line_id in sale_lines)
                        _logger.info("Moves for line %s: %s", line.product_id.name, moves.mapped('id'))
                        for move in moves:
                            for lot in move.lot_ids:
                                # Solo incluir productos con lot_ids
                                unit_lines.append({
                                    'index': len(unit_lines) + 1,
                                    'name': line.product_id.name or 'Unnamed Product',
                                    'price_unit': line.price_unit or 0.0,
                                    'price_subtotal': line.price_subtotal or 0.0,
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
                        'name': f"{self.name}_simple_invoice.pdf",
                        'type': 'binary',
                        'datas': base64.b64encode(custom_pdf_content),
                        'res_model': self._name,
                        'res_id': self.id,
                        'mimetype': 'application/pdf',
                    })
                    attachments.append(custom_attachment.id)
                    _logger.info("Generated simple report for %s: %s", self.name, custom_attachment.name)
                else:
                    _logger.warning("No unit lines generated for %s: no valid invoice lines with lot_ids found", self.name)
        except Exception as e:
            _logger.error("Failed to render custom simple invoice report for %s: %s", self.name, str(e))

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

        if attachments:
            ctx['default_attachment_ids'] = [(6, 0, attachments)]
            _logger.info("Context for mail.compose.message: %s", ctx)

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
        """ Send a mail to the customer with two PDF attachments: the standard invoice report
        and one custom simple report containing one page per product unit with lot_ids.

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
        try:
            # Render the standard invoice report
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

        # Generate one PDF with one page per product unit with lot_ids
        try:
            custom_report_action = self.env.ref('custom_ce_template.action_report_simple_saleorder')
            unit_lines = []
            # Obtener el pedido de venta asociado a la factura
            sale_orders = self.line_ids.mapped('sale_line_ids.order_id')
            if sale_orders:
                # Obtener las entregas asociadas al pedido de venta
                pickings = self.env['stock.picking'].search([('sale_id', 'in', sale_orders.ids), ('state', '=', 'done')])
                _logger.info("Pickings for invoice %s: %s", self.name, pickings.mapped('name'))

                for line in self.line_ids:
                    if not line.display_type and line.quantity > 0:  # Excluir líneas de tipo display y con cantidad 0
                        # Obtener movimientos de inventario asociados a la línea de la factura
                        sale_lines = line.sale_line_ids
                        moves = pickings.mapped('move_ids_without_package').filtered(lambda m: m.sale_line_id in sale_lines)
                        _logger.info("Moves for line %s: %s", line.product_id.name, moves.mapped('id'))
                        for move in moves:
                            for lot in move.lot_ids:
                                # Solo incluir productos con lot_ids
                                unit_lines.append({
                                    'index': len(unit_lines) + 1,
                                    'name': line.product_id.name or 'Unnamed Product',
                                    'price_unit': line.price_unit or 0.0,
                                    'price_subtotal': line.price_subtotal or 0.0,
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
                        'name': f"{self.name}_simple_invoice.pdf",
                        'type': 'binary',
                        'datas': base64.b64encode(custom_pdf_content),
                        'res_model': self._name,
                        'res_id': self.id,
                        'mimetype': 'application/pdf',
                    })
                    attachments.append(custom_attachment.id)
                    _logger.info("Generated simple report for %s: %s", self.name, custom_attachment.name)
                else:
                    _logger.warning("No unit lines generated for %s: no valid invoice lines with lot_ids found", self.name)
        except Exception as e:
            _logger.error("Failed to render custom simple invoice report for %s: %s", self.name, str(e))

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
            _logger.warning("No attachments generated for invoice %s", self.name)

# from odoo import models, api
# import base64
# import logging

# _logger = logging.getLogger(__name__)

# class AccountMove(models.Model):
#     _inherit = 'account.move'

#     def action_invoice_sent(self):
#         """Override to attach custom PDF with product unit and lot info."""
#         self.ensure_one()

#         # Llama al método original
#         action = super().action_invoice_sent()

#         # Generar adjunto PDF personalizado (similar a tu SaleOrder)
#         attachments = []
#         try:
#             custom_report_action = self.env.ref('custom_ce_template.action_report_simple_saleorder')
#             unit_lines = []

#             # Buscar SO vinculado a esta factura
#             sale_orders = self.line_ids.sale_line_ids.order_id
#             pickings = self.env['stock.picking'].search([
#                 ('sale_id', 'in', sale_orders.ids),
#                 ('state', '=', 'done')
#             ])

#             for sale_order in sale_orders:
#                 for line in sale_order.order_line:
#                     if not line.display_type and line.product_uom_qty > 0:
#                         moves = pickings.mapped('move_ids_without_package').filtered(lambda m: m.sale_line_id == line)
#                         for move in moves:
#                             for lot in move.lot_ids:
#                                 unit_lines.append({
#                                     'index': len(unit_lines) + 1,
#                                     'name': line.product_id.name or 'Unnamed Product',
#                                     'price_unit': line.price_unit or 0.0,
#                                     'price_subtotal': line.price_unit or 0.0,
#                                     'default_code': line.product_id.default_code or '',
#                                     'lot_name': lot.name,
#                                 })

#             if unit_lines:
#                 context = self.env.context.copy()
#                 context.update({
#                     'unit_lines': unit_lines,
#                     'lang': self.partner_id.lang or 'es_ES',
#                 })
#                 self = self.with_context(**context)
#                 pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
#                     custom_report_action.report_name, res_ids=self.ids
#                 )
#                 attachment = self.env['ir.attachment'].create({
#                     'name': f"{self.name}_unidad_lotes.pdf",
#                     'type': 'binary',
#                     'datas': base64.b64encode(pdf_content),
#                     'res_model': self._name,
#                     'res_id': self.id,
#                     'mimetype': 'application/pdf',
#                 })
#                 attachments.append(attachment.id)

#         except Exception as e:
#             _logger.error("Error generating custom PDF for invoice %s: %s", self.name, str(e))

#         # Insertar adjuntos al contexto del wizard si existen
#         if attachments and isinstance(action, dict) and 'context' in action:
#             action['context'].update({
#                 'default_attachment_ids': [(6, 0, attachments)]
#             })

#         return action
