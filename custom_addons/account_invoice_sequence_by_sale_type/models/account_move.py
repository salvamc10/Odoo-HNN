from odoo import models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Al crear una factura, se aplica la lógica de asignar secuencia si corresponde.
        """
        moves = super().create(vals_list)
        for move in moves:
            move._set_invoice_sequence_by_template()
        return moves

    def _set_invoice_sequence_by_template(self):
        """
        Asigna automáticamente una secuencia a la factura según la plantilla del pedido de venta.

        Requisitos:
        - Factura cliente (`out_invoice`)
        - Estado borrador
        - Con origen (`invoice_origin`)
        - Sin nombre definido (name vacío, '/', o 'Borrador')
        """
        for record in self:
            if (record.move_type == 'out_invoice' and
                record.invoice_origin and
                record.state == 'draft' and
                (not record.name or record.name in ('/', 'Borrador'))):

                sale_order = self.env['sale.order'].search([
                    ('name', '=', record.invoice_origin)
                ], limit=1)

                if sale_order and sale_order.sale_order_template_id:
                    template_name = sale_order.sale_order_template_id.name
                    sequence_mapping = {
                        'Alquiler': 'sequence_factura_alquiler',
                        'Maquina': 'sequence_factura_maquina',
                        'Recambio': 'sequence_factura_recambio',
                        'Reparacion': 'sequence_factura_reparacion',
                    }
                    sequence_code = sequence_mapping.get(template_name)
                    if sequence_code:
                        sequence = self.env['ir.sequence'].sudo().next_by_code(sequence_code)
                        if sequence:
                            record.sudo().write({'name': sequence})
