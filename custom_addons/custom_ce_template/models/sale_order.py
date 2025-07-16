from odoo import models, SUPERUSER_ID
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_invoice_create(self, grouped=False, final=False, date=None):
        """ Crea la factura, adjunta manuales desde product.template e incluye certificados CE si hay lotes. """
        self.ensure_one()

        # 1. Validación de facturas existentes
        existing_invoices = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('state', '!=', 'cancel'),
        ])
        if existing_invoices:
            _logger.warning("Factura ya existe para %s: %s", self.name, existing_invoices.mapped('name'))
            return existing_invoices.ids

        # 2. Crear factura
        invoice_ids = super().action_invoice_create(grouped=grouped, final=final, date=date)
        invoices = self.env['account.move'].browse(invoice_ids)
        _logger.info("Factura creada para %s: %s", self.name, invoices.mapped('name'))


        # Dentro de action_invoice_create
        for invoice in invoices:
            attachments = []
            for line in self.order_line:
                product_template = line.product_id.product_tmpl_id
                attachment = product_template.invoice_attachment_id
                if attachment:
                    exists = self.env['ir.attachment'].search([
                        ('res_model', '=', 'account.move'),
                        ('res_id', '=', invoice.id),
                        ('datas_fname', '=', attachment.datas_fname),
                    ], limit=1)
                    if not exists:
                        copied = attachment.copy({
                            'res_model': 'account.move',
                            'res_id': invoice.id,
                        })
                        attachments.append(copied.id)
                        _logger.info("Adjunto '%s' copiado a factura %s desde producto %s",
                                     copied.name, invoice.name, product_template.name)
            if attachments:
                invoice.message_post(
                    body="Documentos del producto añadidos automáticamente desde product.template.",
                    attachment_ids=attachments
                )



        # 4. Adjuntar certificado CE (si hay lotes y no existe ya)
        cert_exists = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('name', 'ilike', 'Certificado CE%'),
        ], limit=1)
        if not cert_exists:
            pickings = self.env['stock.picking'].search([
                ('sale_id', '=', self.id),
                ('state', '=', 'done'),
                ('picking_type_id.code', '=', 'outgoing')
            ])

            unit_lines = []
            for line in self.order_line:
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
                try:
                    context = self.env.context.copy()
                    context.update({
                        'unit_lines': unit_lines,
                        'lang': self.partner_id.lang or 'es_ES',
                    })
                    pdf_content, _ = self.env['ir.actions.report'].with_context(**context)._render_qweb_pdf(
                        'custom_ce_template.report_simple_saleorder', res_ids=self.ids
                    )
                    self.env['ir.attachment'].create({
                        'name': f"Certificado CE - {self.name}.pdf",
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': 'sale.order',
                        'res_id': self.id,
                        'mimetype': 'application/pdf',
                    })
                    _logger.info("Certificado CE generado para %s", self.name)
                except Exception as e:
                    _logger.error("Error generando Certificado CE para %s: %s", self.name, str(e))
            else:
                _logger.info("No se generó Certificado CE: sin productos con lote en %s", self.name)
        else:
            _logger.info("Certificado CE ya existe para %s", self.name)

        return invoice_ids
