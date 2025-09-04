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

    @api.depends('location_id', 'location_dest_id', 'state', 'picked')
    def _compute_estado_recambio(self):
        """
        Calcula el estado del recambio basado en:
        - La ubicación actual y destino del producto
        - Si está marcado como usado (picked)
        - El estado del movimiento
        """
        for record in self:
            estado = False
            
            # Si está marcado como usado, siempre será Montado/servido
            if record.picked:
                estado = 'Montado/servido'
                record.estado_recambio = estado
                continue

            # Ubicación actual y destino
            location = record.location_id
            location_dest = record.location_dest_id

            # Si no hay ubicación, no podemos determinar el estado

            if not location:
                record.estado_recambio = estado
                continue


            # Determinar estado basado en ubicación y tipo de ubicación
            if location.usage == 'internal':
                # Es una ubicación interna (almacén)
                if location.complete_name and 'stock' in location.complete_name.lower():
                    estado = 'Stock'
                else:
                    estado = 'Estanteria'
            elif location.usage == 'supplier':
                # Viene de proveedor
                estado = 'Pte almacenar'
            elif location.usage == 'customer':
                # Está en cliente
                if record.state == 'done':
                    estado = 'Montado/servido'
                else:
                    estado = 'Stock'
            elif location.usage == 'production':
                # Está en reparación
                if location_dest.usage == 'customer':
                    estado = 'Montado/servido'
                else:
                    estado = 'Stock'
            
            record.estado_recambio = estado

