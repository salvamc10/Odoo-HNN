# -*- coding: utf-8 -*-
from odoo import models, fields, api # type: ignore

class StockLotInherit(models.Model):
    _inherit = 'stock.lot'

    employee_assigned_ids = fields.Many2many(
        'hr.employee',
        string='Empleados Asignados',
        related='workorder_id.employee_assigned_ids',
        readonly=False
    )
    
    workorder_id = fields.Many2one(
        'mrp.workorder',
        compute='_compute_workorder_id',
        string='Orden de Trabajo',
        store=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        readonly=False
    )

    state = fields.Selection([
        ('reception', 'Recepción'),
        ('manufacturing', 'Fabricación'),
        ('in_stock', 'Terminada'),
        ('scrapped', 'Canibalizada'),
        ('in_transit', 'Vendida'),
        ('rental', 'Alquilada'),
    ], string='Estado', compute='_compute_state', store=True)

    # Relación con workorders que tienen este lote como terminado
    mrp_workorder_ids = fields.One2many(
        'mrp.workorder',
        'finished_lot_id',
        string='Órdenes de trabajo asociadas'
    )

    # Operaciones pendientes de calidad durante la fabricación
    # Cambio campo realizado por Pedro 05/06/2025 
    mrp_order_pending = fields.Integer(
        string='Operaciones de Fabricación',
        compute='_compute_mrp_order_pending',
        store=False # Cambio realizado por Pedro 03/06/2025
    )

    # Operaciones pendientes de calidad en la salida
    quality_operations_outgoing = fields.Integer(
        string='Operaciones de Salida',
        compute='_compute_quality_operations_outgoing',
        store=True # Cambio realizado por Pedro 03/06/2025
    )  

    note = fields.Text(
            string='Notas',
    )

    @api.depends('location_id', 'mrp_workorder_ids.state')
    def _compute_state(self):
        """
        Calcula el estado basado en el tipo de ubicación, si es de desecho,
        y si la ubicación interna corresponde a 'Alquiler'.
        Además, si la ubicación es de fabricación ('production'), el estado
        depende también del estado de las órdenes de trabajo asociadas.
        """
        for lot in self:
            location = lot.location_id
            
            # Primero verificar si hay órdenes de trabajo activas (independientemente de la ubicación)
            active_workorders = lot.mrp_workorder_ids.filtered(
                lambda w: w.state not in ('done', 'cancel')
            )
            
            # Si hay workorders activos, el estado es manufacturing (prioritario)
            if active_workorders:
                lot.state = 'manufacturing'
                continue
            
            # Si no hay ubicación, estado por defecto
            if not location:
                lot.state = 'in_stock'
                continue

            # Verificar estados basados en ubicación
            if location.scrap_location:
                lot.state = 'scrapped'
            elif location.usage == 'supplier':
                lot.state = 'reception'
            elif location.usage == 'production':
                # Si está en ubicación de producción pero no hay workorders activos
                lot.state = 'in_stock'
            elif location.usage == 'customer':
                lot.state = 'in_transit'
            elif location.usage == 'internal':
                # Verificar si es ubicación de alquiler
                # Buscar "Alquiler" en cualquier parte de la ruta completa de la ubicación
                location_path = location.complete_name or location.name or ''
                if 'alquiler' in location_path.lower():
                    lot.state = 'rental'
                else:
                    lot.state = 'in_stock'
            else:
                lot.state = 'manufacturing'

    # Modificado modulo para calcular las operaciones de fabricación pendientes, Pedro 05/06/2025
    @api.depends('mrp_workorder_ids.state')
    def _compute_mrp_order_pending(self):
        for record in self:
            active_workorders = record.mrp_workorder_ids.filtered(
                lambda w: w.state not in ('done', 'cancel')
            )
            record.mrp_order_pending = len(active_workorders)

    @api.depends('name')
    def _compute_quality_operations_outgoing(self):
        """ Calcula cuántas operaciones de calidad quedan pendientes para la salida. """
        for lot in self:
            # Buscar las líneas de movimiento relacionadas al lote
            move_lines = self.env['stock.move.line'].search([
                ('lot_id', '=', lot.id)
            ])

            # A partir de esas líneas, identificamos los `pickings` de salida (outgoing)
            picking_ids = move_lines.mapped('picking_id').filtered(lambda p: p.picking_type_id.code == 'outgoing')

            if picking_ids:
                # Buscar los controles de calidad asociados y pendientes
                quality_checks = self.env['quality.check'].search([
                    ('picking_id', 'in', picking_ids.ids),
                    ('quality_state', 'not in', ['pass'])
                ])
                # Contar los que están pendientes
                lot.quality_operations_outgoing = len(quality_checks)
            else:
                lot.quality_operations_outgoing = 0

    @api.depends('name')
    def _compute_workorder_id(self):
        for lot in self:
            production = self.env['mrp.production'].search([
                ('lot_producing_id', '=', lot.id)
            ], limit=1)
    
            if production:
                workorder = self.env['mrp.workorder'].search([
                    ('production_id', '=', production.id)
                ], limit=1)
                lot.workorder_id = workorder.id if workorder else False
            else:
                lot.workorder_id = False
