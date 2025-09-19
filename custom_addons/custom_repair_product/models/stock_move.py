from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


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
        compute='_compute_estado_recambio',
        store=True
    )

    x_forecast_state = fields.Selection(
        selection=[
            ('available', 'Disponible'),
            ('forecasted', 'Pronosticado'),
            ('unavailable', 'No disponible'),
        ],
        string="Estado de disponibilidad",
        compute='_compute_forecast_state_and_date',
        store=True,
        compute_sudo=False,
    )

    x_earliest_forecast_date = fields.Datetime(
        string="Fecha prevista más temprana",
        compute='_compute_forecast_state_and_date',
        store=True,
        compute_sudo=False,
    )

    @api.depends('forecast_availability', 'product_uom_qty', 'state', 'product_id', 'picking_id', 'picking_id.state', 'forecast_expected_date', 'picking_id.scheduled_date')
    def _compute_forecast_state_and_date(self):
        for record in self:
            # Skip done or cancelled moves
            if record.state in ('done', 'cancel') or not record.product_id or record.product_uom_qty <= 0:
                record.x_forecast_state = 'available'
                record.x_earliest_forecast_date = False
                _logger.debug(f"Move {record.id}: Skipped (state={record.state}, product_id={record.product_id.id}, qty={record.product_uom_qty})")
                continue

            has_unavailable = False
            has_forecasted = False
            earliest_date = False

            # Check if the current move is unavailable
            if record.forecast_availability < record.product_uom_qty:
                has_unavailable = True
            else:
                # Check for pending incoming moves (confirmed purchase not validated)
                incoming_moves = self.env['stock.move'].search([
                    ('product_id', '=', record.product_id.id),
                    ('state', 'in', ('confirmed', 'assigned', 'partially_available')),
                    ('picking_type_id.code', '=', 'incoming'),
                    ('id', '!=', record.id),
                    ('picking_id.state', '!=', 'done'),
                ])
                if incoming_moves:
                    has_forecasted = True
                    # Get earliest forecast_expected_date or fallback to scheduled_date
                    for inc in incoming_moves:
                        date = inc.forecast_expected_date or inc.picking_id.scheduled_date
                        if date and (not earliest_date or date < earliest_date):
                            earliest_date = date
                            _logger.debug(f"Move {record.id}: Incoming Move {inc.id}, Date={date}")

            # Set state
            if has_unavailable and not has_forecasted:
                record.x_forecast_state = 'unavailable'
            elif has_forecasted:
                record.x_forecast_state = 'forecasted'
            else:
                record.x_forecast_state = 'available'

            record.x_earliest_forecast_date = earliest_date
            _logger.debug(f"Move {record.id}: State={record.x_forecast_state}, Date={record.x_earliest_forecast_date}")    

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

    def action_add_to_consultas_lines(self):
        """Añade la pieza consultada a las líneas de consulta."""
        self.ensure_one()
        if not self.product_id:
            return
            
        repair_order = self.repair_id  # Cambiado de repair_order_id a repair_id
        if repair_order:
            # Crear el registro en repair.consulta
            self.env['repair.consulta'].create({
                'repair_order_id': repair_order.id,  # Asegúrate de usar repair_order_id aquí, ya que es el campo en repair.consulta
                'product_id': self.product_id.id,
                'product_uom_qty': self.product_uom_qty or 0.0,
                'refer': self.product_id.default_code or '',
            })
            # Eliminar la pieza después de añadirla
            self.unlink()
