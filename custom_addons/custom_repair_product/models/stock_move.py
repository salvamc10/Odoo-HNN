from odoo import fields, models, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one(
        'stock.lot', 
        string="Lot/Serial Number", 
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]"
    )
    repair_state = fields.Selection(
        related='repair_id.state', 
        store=True, 
        string="Estado reparación"
    )
    partner_repair_id = fields.Many2one(
        related='repair_id.partner_id', 
        string="Cliente", 
        store=True
    )
    consulta_text = fields.Char(string='Consulta')
    x_machine_number = fields.Char(
        related='lot_id.x_machine_number', 
        string="Número de Máquina/Lote", 
        store=True
    )
    internal_reference = fields.Char(
        related='lot_id.ref', 
        string="Referencia Interna", 
        store=True
    )    
    
    provider_id = fields.Many2one(
        'product.supplierinfo', 
        string="Proveedor", 
        compute='_compute_provider_id', 
        store=True
    )
    provider_reference = fields.Char(
        related='provider_id.product_code', 
        string="Referencia Proveedor", 
        store=True
    )
    provider_ids = fields.One2many(
        related='product_id.seller_ids', 
        string="Proveedores", 
        readonly=True
    )
    
    estado_recambio = fields.Selection(
        string="Estado Recambio",
        selection=[
            ('Pte almacenar', 'Pte de almacenar'), 
            ('Estanteria', 'Estanteria'),
            ('Stock', 'Stock'),
            ('Montado/servido', 'Montado/servido')
        ],
        compute='_compute_estado_recambio',  # ✅ CORREGIDO
        store=True
    )

    @api.depends('product_id')
    def _compute_provider_id(self):
        """Calcula el proveedor principal del producto"""
        for record in self:
            if record.product_id and record.product_id.seller_ids:
                # Tomar el primer proveedor disponible
                record.provider_id = record.product_id.seller_ids[0]
            else:
                record.provider_id = False

    @api.depends('location_id', 'picked')
    def _compute_estado_recambio(self):
        """
        Calcula el estado del recambio basado en la ubicación y si está marcado como usado (picked).
        """
        for record in self:
            estado = False
            location = record.location_id

            if not location:
                record.estado_recambio = estado
                continue

            # 1. Montado/servido: Si el recambio está marcado como usado
            if record.picked:
                estado = 'Montado/servido'
            # 2. Stock: Si la ubicación es la principal de stock
            elif location.usage == 'internal' and location.name.lower() == 'stock':
                estado = 'Stock'
            # 3. Pte almacenar: Si la ubicación es 'input' (recepción en 2 pasos)
            elif location.usage == 'input':
                estado = 'Pte almacenar'
            # 4. Estanteria: Cualquier otra ubicación interna distinta de 'stock'
            elif location.usage == 'internal':
                estado = 'Estanteria'

            record.estado_recambio = estado