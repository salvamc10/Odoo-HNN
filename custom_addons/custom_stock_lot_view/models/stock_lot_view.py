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
        ('in_stock', 'En Stock'),
        ('scrapped', 'Desechado'),
        ('in_transit', 'Vendida'),
    ], string='Estado', compute='_compute_state', store=True)

    # Operaciones pendientes de calidad durante la fabricación
    quality_operations_pending = fields.Integer(
        string='Operaciones de Fabricación',
        compute='_compute_quality_operations_pending',
        store=False
    )

    # Operaciones pendientes de calidad en la salida
    quality_operations_outgoing = fields.Integer(
        string='Operaciones de Salida',
        compute='_compute_quality_operations_outgoing',
        store=False
    )

    note = fields.Text(
            string='Notas',
    )

    @api.depends('location_id')
    def _compute_state(self):
        """ Calcula el estado basado en el tipo de ubicación, eliminando dependencia de nombres fijos. """
        for lot in self:
            location = lot.location_id
            if not location:
                lot.state = 'in_stock'
                continue
            if location.usage == 'supplier':
                lot.state = 'reception'
            elif location.usage == 'production':
                lot.state = 'manufacturing'
            elif location.usage == 'inventory':
                scrap_location = self.env.ref('stock.stock_location_scrapped', raise_if_not_found=False)
                if scrap_location and location.id == scrap_location.id:
                    lot.state = 'scrapped'
                else:
                    lot.state = 'in_stock'
            elif location.usage == 'customer':
                lot.state = 'in_transit'
            else:
                lot.state = 'in_stock'

    @api.depends('name')
    def _compute_quality_operations_pending(self):
        """ Calcula cuántas operaciones de calidad quedan pendientes para este lote. """
        for lot in self:
            # Encontrar la producción asociada
            production = self.env['mrp.production'].search([
                ('lot_producing_id', '=', lot.id)
            ], limit=1)

            if production:
                # Buscar los controles de calidad relacionados con las órdenes de trabajo de esa producción
                quality_checks = self.env['quality.check'].search([
                    ('workorder_id.production_id', '=', production.id),
                    ('quality_state', 'not in', ['pass'])
                ])
                # Contar los que están pendientes
                lot.quality_operations_pending = len(quality_checks)
            else:
                lot.quality_operations_pending = 0

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