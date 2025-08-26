from odoo import fields, models, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number", domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")
    consulta_text = fields.Char(string='Consulta')
    x_machine_number = fields.Char(related='lot_id.x_machine_number', string="Número de Máquina/Lote", store=True)
    internal_reference = fields.Char(related='lot_id.ref', string="Referencia Interna", store=True)    
    provider_reference = fields.Char(related='provider_id.product_code', string="Referencia Proveedor", store=True)
    provider_id = fields.Many2one('product.supplierinfo', string="Proveedor", domain="[('supplier_rank', '>', 0)]")
    description = fields.Html(related='lot_id.note', string="Descripción", store=True)
    estado_recambio = fields.Selection(
            string="Estado Recambio",
            selection=[('Pte almacenar', 'Pte de almacenar'), 
                       ('Estanteria', 'Estanteria'),
                       ('Stock', 'Stock'),
                       ('Montado/servido', 'Montado/servido')],
            ondelete={'Pte almacenar': 'cascade', 'Estanteria': 'cascade', 'Stock': 'cascade', 'Montado/servido': 'cascade'},
            compute='_onchange_estado_recambio',
            store=True
            readonly=False
        )

    @api.depends('picked', 'location_id', 'location_id.usage', 'location_id.location_id', 'state', 'picking_type_id', 'picking_id')
    def _compute_estado_recambio(self):
        for record in self:
            # Caso 1: Montado/servido si picked = True
            if record.picked:
                record.estado_recambio = 'Montado/servido'
            # Caso 2: Pte almacenar para recepción en 2 pasos
            elif (record.state == 'done' and
                  record.picking_type_id.code == 'incoming' and
                  record.picking_id and
                  record.picking_id.move_lines.filtered(lambda m: m.state == 'assigned')):
                record.estado_recambio = 'Pte almacenar'
            # Caso 3: Estanteria si la ubicación es una sububicación interna
            elif (record.location_id.usage == 'internal' and
                  record.location_id.location_id and
                  record.location_id.location_id.usage == 'internal'):
                record.estado_recambio = 'Estanteria'
            # Caso 4: Stock si la ubicación es la raíz interna
            elif (record.location_id.usage == 'internal' and
                  (not record.location_id.location_id or
                   record.location_id.location_id.usage != 'internal')):
                record.estado_recambio = 'Stock'
            else:
                record.estado_recambio = False

    @api.onchange('estado_recambio')
    def _onchange_estado_recambio(self):
        for record in self:
            if record.estado_recambio == 'Montado/servido':
                record.picked = True