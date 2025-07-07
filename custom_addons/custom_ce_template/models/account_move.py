from odoo import models, api
import base64
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_invoice_sent(self):
        """Override to attach custom PDF with product unit and lot info."""
        self.ensure_one()

        # Llama al método original
        action = super().action_invoice_sent()

        # Generar adjunto PDF personalizado (similar a tu SaleOrder)
        attachments = []
        try:
            custom_report_action = self.env.ref('custom_ce_template.action_report_simple_saleorder')
            unit_lines = []

            # Buscar SO vinculado a esta factura
            sale_orders = self.line_ids.sale_line_ids.order_id
            pickings = self.env['stock.picking'].search([
                ('sale_id', 'in', sale_orders.ids),
                ('state', '=', 'done')
            ])

            for sale_order in sale_orders:
                for line in sale_order.order_line:
                    if not line.display_type and line.product_uom_qty > 0:
                        moves = pickings.mapped('move_ids_without_package').filtered(lambda m: m.sale_line_id == line)
                        for move in moves:
                            for lot in move.lot_ids:
                                unit_lines.append({
                                    'index': len(unit_lines) + 1,
                                    'name': line.product_id.name or 'Unnamed Product',
                                    'price_unit': line.price_unit or 0.0,
                                    'price_subtotal': line.price_unit or 0.0,
                                    'default_code': line.product_id.default_code or '',
                                    'lot_name': lot.name,
                                })

            if unit_lines:
                context = self.env.context.copy()
                context.update({
                    'unit_lines': unit_lines,
                    'lang': self.partner_id.lang or 'es_ES',
                })
                self = self.with_context(**context)
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                    custom_report_action.report_name, res_ids=self.ids
                )
                attachment = self.env['ir.attachment'].create({
                    'name': f"{self.name}_unidad_lotes.pdf",
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                })
                attachments.append(attachment.id)

        except Exception as e:
            _logger.error("Error generating custom PDF for invoice %s: %s", self.name, str(e))

        # Insertar adjuntos al contexto del wizard si existen
        if attachments and isinstance(action, dict) and 'context' in action:
            action['context'].update({
                'default_attachment_ids': [(6, 0, attachments)]
            })

        return action
