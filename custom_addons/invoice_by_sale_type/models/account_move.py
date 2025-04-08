from odoo import models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        '''
        Reemplaza la acción de Studio que asignaba secuencia a la factura según
        la plantilla del pedido de venta asociado, si estaba en borrador.
        '''
        for record in self:
            if (
                record.invoice_origin
                and record.state == 'draft'
                and (not record.name or record.name in ('/', 'Borrador'))
            ):
                sale_order = self.env['sale.order'].search(
                    [('name', '=', record.invoice_origin)], limit=1
                )
                if sale_order and sale_order.sale_order_template_id:
                    template_name = sale_order.sale_order_template_id.name
                    sequence_mapping = {
                        'Alquiler': 'sequence_factura_alquiler',
                        'Maquina': 'sequence_factura_maquina',
                        'Recambio': 'sequence_factura_recambio',
                        'Reparacion': 'sequence_factura_reparacion',
                    }
                    sequence_id = sequence_mapping.get(template_name)
                    if sequence_id:
                        sequence = self.env['ir.sequence'].sudo().next_by_code(sequence_id)
                        if sequence:
                            vals['name'] = sequence
        return super().write(vals)
