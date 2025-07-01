from odoo import models, api
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        self.filtered(lambda so: so.state in ('draft', 'sent')).order_line._validate_analytic_distribution()
        lang = self.env.context.get('lang')

        ctx = {
            'default_model': 'sale.order',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'email_notification_allow_footer': True,
            'proforma': self.env.context.get('proforma', False),
        }

        # Detectamos si hay una sola orden o varias
        if len(self) == 1:
            ctx.update({
                'force_email': True,
                'model_description': self.with_context(lang=lang).type_name,
            })

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

            # ==>> 🔥 Aquí inyectamos nuestra lógica de generación CE
            ce_attachment_ids = []
            try:
                report = self.env.ref('custom_ce_template.report_ce_document_stock_action').sudo()
                for picking in self.picking_ids.filtered(lambda p: p.state in ['assigned', 'done']):
                    for move_line in picking.move_line_ids:
                        product = move_line.product_id
                        lot = move_line.lot_id

                        if product.tracking == 'serial' and lot:
                            pdf_content, _ = report._render_qweb_pdf(move_line.id)
                            filename = f"CE_{product.display_name}_{lot.name}.pdf"

                            attachment = self.env['ir.attachment'].create({
                                'name': filename,
                                'datas': base64.b64encode(pdf_content),
                                'res_model': 'sale.order',
                                'res_id': self.id,
                                'mimetype': 'application/pdf',
                                'type': 'binary',
                            })
                            ce_attachment_ids.append(attachment.id)
            except Exception as e:
                _logger.error(f"Error generando hojas CE para {self.name}: {str(e)}")

            if ce_attachment_ids:
                ctx['default_attachment_ids'] = [(6, 0, ce_attachment_ids)]

        else:
            ctx['default_composition_mode'] = 'mass_mail'

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

        # Layout wizard de configuración de plantilla
        if (
            self.env.context.get('check_document_layout')
            and not self.env.context.get('discard_logo_check')
            and self.env.is_admin()
            and not self.env.company.external_report_layout_id
        ):
            layout_action = self.env['ir.actions.report']._action_configure_external_report_layout(action)
            action.pop('close_on_report_download', None)
            layout_action['context']['dialog_size'] = 'extra-large'
            return layout_action

        return action

def _get_serial_numbers_grouped(self):
    self.ensure_one()
    serials = []
    for picking in self.picking_ids.filtered(lambda p: p.state == 'done'):
        for move_line in picking.move_line_ids.filtered(lambda l: l.lot_id):
            for i in range(int(move_line.qty_done)):
                serials.append({
                    'product': move_line.product_id,
                    'lot': move_line.lot_id,
                })
    return serials
