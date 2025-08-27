from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number", 
                           domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]")
    repair_state = fields.Selection(related='repair_id.state', store=True, string="Estado reparación")
    partner_repair_id = fields.Many2one(related='repair_id.partner_id', string="Cliente", store=True)
    consulta_text = fields.Char(string='Consulta')
    x_machine_number = fields.Char(related='lot_id.x_machine_number', 
                                  string="Número de Máquina/Lote", store=True)
    internal_reference = fields.Char(related='lot_id.ref', string="Referencia Interna", store=True)    
    
    @api.depends('product_id')
    def _compute_provider_id(self):
        for record in self:
            if record.product_id:
                supplier = record.product_id.seller_ids.filtered(lambda s: s.sequence == 0) or record.product_id.seller_ids[:1]
                record.provider_id = supplier.id if supplier else False

    provider_id = fields.Many2one('product.supplierinfo', string="Proveedor", compute='_compute_provider_id', store=True)
    
    provider_reference = fields.Char(related='provider_id.product_code', 
                                   string="Referencia Proveedor", store=True)
    provider_ids = fields.One2many(
        related='lot_id.product_id.seller_ids',
        string="Proveedores",
        readonly=True
    )
    description = fields.Html(related='lot_id.note', string="Descripción", store=True)
    estado_recambio = fields.Selection(
        string="Estado Recambio",
        selection=[
            ('Pte almacenar', 'Pte de almacenar'), 
            ('Estanteria', 'Estanteria'),
            ('Stock', 'Stock'),
            ('Montado/servido', 'Montado/servido')
        ],
        ondelete={
            'Pte almacenar': 'cascade', 
            'Estanteria': 'cascade', 
            'Stock': 'cascade', 
            'Montado/servido': 'cascade'
        },
        compute='_compute_estado_recambio',
        store=True,
        readonly=False
    )

    @api.depends('location_dest_id', 'location_id', 'state', 'picked')
    def _compute_estado_recambio(self):
        """
        Computa el estado del recambio basado únicamente en la ubicación y el estado picked
        """
        for record in self:
            estado = False

            # 1. Montado/servido: Si picked está marcado o es un movimiento a cliente
            if record.picked or (record.state == 'done' and record.location_dest_id and record.location_dest_id.usage == 'customer'):
                estado = 'Montado/servido'

            # 2. Pte almacenar: Si es un movimiento completado a la ubicación de entrada (Input)
            elif (record.state == 'done' and record.location_dest_id and record.location_dest_id.usage == 'input'):
                estado = 'Pte almacenar'

            # 3. Stock: Si es un movimiento completado a la ubicación principal de stock
            elif (record.state == 'done' and record.location_dest_id and record.location_dest_id == record.location_dest_id.warehouse_id.lot_stock_id):
                estado = 'Stock'

            # 4. Estanteria: Si es un movimiento completado a cualquier otra ubicación interna distinta de Stock
            elif (record.state == 'done' and record.location_dest_id and record.location_dest_id.usage == 'internal' and 
                  record.location_dest_id != record.location_dest_id.warehouse_id.lot_stock_id):
                estado = 'Estanteria'

            record.estado_recambio = estado

    @api.onchange('estado_recambio')
    def _onchange_estado_recambio(self):
        """
        Marca como picked cuando el estado es Montado/servido
        """
        for record in self:
            if record.estado_recambio == 'Montado/servido':
                record.picked = True