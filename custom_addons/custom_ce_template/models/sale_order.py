from odoo import models, SUPERUSER_ID
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    #     """ Mark the given draft quotation(s) as sent """
    #     if any(order.state != 'draft' for order in self):
    #         raise UserError(_("Only draft orders can be marked as sent directly."))

    #     for order in self:
    #         order.message_subscribe(partner_ids=order.partner_id.ids)

    #     self.write({'state': 'sent'})

    def action_invoice_create(self, grouped=False, final=False, date=None):
        """ Create invoice and generate CE certificate if needed """
        self.ensure_one()
        
        existing_invoices = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('state', '!=', 'cancel'),
        ])
        if existing_invoices:
            _logger.warning("Invoice already exists for sale order %s: %s", self.name, existing_invoices.mapped('name'))
            return existing_invoices.ids

        invoice_ids = super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final, date=date)
        _logger.info("Invoice created for sale order %s (ID: %s)", self.name, invoice_ids)

        # Verificar si ya existe el certificado
        existing = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('name', 'ilike', 'Certificado CE%'),
        ], limit=1)

        if existing:
            _logger.info("Certificado CE ya existe para %s. No se volverá a generar.", self.name)
            return invoice_ids

        # Buscar pickings realizados
        pickings = self.env['stock.picking'].search([
            ('sale_id', '=', self.id),
            ('state', '=', 'done'),
            ('picking_type_id.code', '=', 'outgoing')
        ])

        unit_lines = []
        for picking in pickings:
            for move in picking.move_lines:
                if move.lot_ids:
                    for lot in move.lot_ids:
                        unit_lines.append({
                            'index': len(unit_lines) + 1,
                            'name': move.product_id.name or 'Unnamed Product',
                            'price_unit': move.sale_line_id.price_unit or 0.0,
                            'price_subtotal': move.sale_line_id.price_subtotal or 0.0,
                            'default_code': move.product_id.default_code or '',
                            'lot_name': lot.name,
                        })

        if unit_lines:
            context = self.env.context.copy()
            context.update({
                'unit_lines': unit_lines,
                'lang': self.partner_id.lang or 'es_ES',
            })
            custom_pdf_content, _ = self.env['ir.actions.report'].with_context(**context)._render_qweb_pdf(
                'custom_ce_template.report_simple_saleorder', res_ids=self.ids
            )
            self.env['ir.attachment'].create({
                'name': f"Certificado CE - {self.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(custom_pdf_content),
                'res_model': 'sale.order',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            _logger.info("Certificado CE generado para %s durante creación de factura", self.name)
        else:
            _logger.warning("No se generó certificado CE para %s: no se encontraron lotes en entregas", self.name)

        return invoice_ids
