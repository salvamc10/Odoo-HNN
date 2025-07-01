from odoo import models, api
import base64
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            if picking.picking_type_code == 'outgoing':
                picking._generate_ce_documents()
        return res

    def _generate_ce_documents(self):
        try:
            report = self.env.ref('custom_ce_template.report_ce_document_stock_action')
        except ValueError:
            _logger.error("No se encontró el reporte 'custom_ce_template.report_ce_document_stock_action'")
            return

        Attachment = self.env['ir.attachment']

        for move_line in self.move_line_ids:
            lot = move_line.lot_id
            product = move_line.product_id

            _logger.info(f"Procesando línea: {product.display_name}, Lote: {lot.name if lot else 'Sin lote'}")

            if product.tracking != 'none':
                sale_line = move_line.move_id.sale_line_id
                if not sale_line:
                    _logger.warning(f"No se encontró sale_line para {product.display_name}")
                    continue

                if self.sale_id:
                    try:
                        pdf_content, _ = report._render_qweb_pdf(move_line.id)
                        if not pdf_content:
                            _logger.error(f"No se generó contenido PDF para {product.display_name}")
                            continue

                        filename = f"CE_{product.display_name}_{lot.name if lot else 'NOLot'}.pdf"

                        Attachment.create({
                            'name': filename,
                            'datas': base64.b64encode(pdf_content).decode('utf-8'),
                            'res_model': 'sale.order',
                            'res_id': self.sale_id.id,
                            'mimetype': 'application/pdf',
                            'type': 'binary',
                        })

                        _logger.info(f"CE generado y vinculado al pedido de venta {self.sale_id.name}")

                    except Exception as e:
                        _logger.error(f"Error generando CE para {product.display_name}: {str(e)}")


