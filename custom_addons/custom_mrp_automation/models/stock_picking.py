# -*- coding: utf-8 -*-
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()

        for record in self:
            # Solo ejecutamos si es una recepción entrante y ya está en estado 'done'
            if record.picking_type_id.code == 'incoming' and record.state == 'done':
                try:
                    record._run_mrp_automation()
                except Exception as e:
                    _logger.error("Error en la automatización de MRP: %s", str(e))
                    record.message_post(body="❌ Error en automatización de MRP: {}".format(str(e)))

        return res

    def _run_mrp_automation(self):
        existing_mos = self.env['mrp.production'].search([('origin', '=', self.name)])
        if existing_mos:
            self.message_post(body="⚠️ Ya existen órdenes de fabricación asociadas a esta recepción: {}".format(
                ", ".join(existing_mos.mapped('name'))))
            return

        self.message_post(body="🔄 Iniciando automatización de órdenes de fabricación...")        
        related_pickings = self.env['stock.picking'].search([
            ('picking_type_id.code', '=', 'incoming'),
            ('state', '=', 'done'),
            ('origin', '=', self.origin),
        ])
        
        # Recopilar TODOS los componentes recibidos (con y sin números serie)
        received_components = {}
        total_components = 0
        components_with_lots = 0
        components_without_lots = 0

        for picking in related_pickings:
            for line in picking.move_line_ids:
                if line.qty_done > 0:
                    total_components += 1
                    product_id = line.product_id.id
        
                    if product_id not in received_components:
                        received_components[product_id] = []
        
                    if line.lot_id:
                        components_with_lots += 1
                        for _ in range(int(line.qty_done)):
                            received_components[product_id].append({
                                'lot_id': line.lot_id.id,
                                'product_id': product_id,
                                'uom_id': line.product_uom_id.id,
                                'has_lot': True,
                            })
                    else:
                        components_without_lots += 1
                        for _ in range(int(line.qty_done)):
                            received_components[product_id].append({
                                'lot_id': False,
                                'product_id': product_id,
                                'uom_id': line.product_uom_id.id,
                                'has_lot': False,
                            })

        if not received_components:
            self.message_post(body="❌ No se encontraron componentes recibidos")
        else:
            debug_msg = "✅ Componentes recibidos: {} tipos diferentes<br/>".format(len(received_components))
            debug_msg += "📊 Total líneas: {} ({} con lotes, {} sin lotes)<br/>".format(total_components, components_with_lots, components_without_lots)

            env = self.env
            for prod_id, components in received_components.items():
                product_name = env['product.product'].browse(prod_id).name
                with_lots = sum(1 for c in components if c['has_lot'])
                without_lots = sum(1 for c in components if not c['has_lot'])
                debug_msg += "• {}: {} unidades".format(product_name, len(components))
                if with_lots > 0 and without_lots > 0:
                    debug_msg += " ({} con lote, {} sin lote)".format(with_lots, without_lots)
                elif with_lots > 0:
                    debug_msg += " (con lotes)"
                else:
                    debug_msg += " (sin lotes)"
                debug_msg += "<br/>"

            self.message_post(body=debug_msg)

            # Buscar BOMs que contengan alguno de los componentes recibidos
            bom_model = env['mrp.bom']
            mrp_model = env['mrp.production']

            # Buscar BOMs que contengan los productos recibidos como componentes
            matching_boms = []
            for product_id in received_components.keys():
                bom_lines = env['mrp.bom.line'].search([('product_id', '=', product_id)])
                for bom_line in bom_lines:
                    if bom_line.bom_id not in matching_boms:
                        matching_boms.append(bom_line.bom_id)

            self.message_post(body="🔍 BOMs encontradas que usan estos componentes: {}".format(len(matching_boms)))

            if not matching_boms:
                self.message_post(body="⚠️ No se encontraron BOMs que utilicen los componentes recibidos")
            else:
                orders_created = 0

                # Para cada BOM encontrada, verificar si podemos fabricar productos
                for bom in matching_boms:
                    self.message_post(body="📋 Evaluando BOM: {}".format(bom.display_name))

                    # Mapear todos los componentes de esta BOM
                    bom_components = {}  # {product_id: cantidad_requerida}
                    missing_components = []
                    available_components = {}

                    for bom_line in bom.bom_line_ids:
                        comp_id = bom_line.product_id.id
                        bom_components[comp_id] = bom_line.product_qty

                        if comp_id in received_components:
                            available_components[comp_id] = bom_line.product_qty
                        else:
                            missing_components.append(bom_line.product_id.name)

                    if not available_components:
                        self.message_post(body="⚠️ {}: No contiene ninguno de los componentes recibidos".format(bom.display_name))
                        continue

                    # Mostrar información de componentes
                    if missing_components:
                        missing_text = ', '.join(missing_components[:3])
                        if len(missing_components) > 3:
                            missing_text += '...'
                        self.message_post(body="ℹ️ {}: Componentes faltantes: {}".format(bom.display_name, missing_text))

                    available_list = []
                    for comp_id in available_components.keys():
                        comp_name = env['product.product'].browse(comp_id).name
                        available_list.append(comp_name)
                    available_text = ', '.join(available_list[:3])
                    if len(available_list) > 3:
                        available_text += '...'
                    self.message_post(body="✅ {}: Componentes disponibles: {}".format(bom.display_name, available_text))

                    # OPCIÓN 1: Requiere todos los componentes
                    if missing_components:
                        self.message_post(body="⚠️ {}: Saltando BOM - faltan componentes requeridos".format(bom.display_name))
                        continue 

                    # Calcular cuántas unidades podemos fabricar
                    max_units = 999999  
                    for comp_id, required_qty in bom_components.items():
                        if comp_id in received_components:
                            available_qty = len(received_components[comp_id])
                            if required_qty > 0:
                                possible_units = int(available_qty / required_qty)
                                if possible_units < max_units:
                                    max_units = possible_units
                        else:
                            # Si falta un componente, no podemos fabricar
                            max_units = 0
                            break

                    # Crear órdenes de fabricación
                    if max_units > 0 and max_units < 999999:
                        self.message_post(body="🏭 {}: Creando {} órdenes...".format(bom.display_name, max_units))

                        # Hacer una copia de received_components para esta BOM
                        temp_components = {}
                        for k, v in received_components.items():
                            temp_components[k] = v[:]

                        for unit_num in range(max_units):
                            try:
                                # Crear la orden de fabricación
                                product = bom.product_tmpl_id.product_variant_id

                                mo = mrp_model.with_context(no_create_moves=True, skip_auto_confirm=True).create({
                                    'product_id': product.id,
                                    'product_qty': 1,
                                    'product_uom_id': product.uom_id.id,
                                    'bom_id': bom.id,
                                    'origin': self.name,
                                })

                                mo.write({
                                        'state': 'draft',
                                        'product_qty': 1,
                                    })
                                orders_created += 1

                                # Asignar números de serie/lotes a los componentes que los tengan
                                for move_raw in mo.move_raw_ids:
                                    comp_id = move_raw.product_id.id
                                    if comp_id in temp_components and temp_components[comp_id]:
                                        # Obtener la cantidad requerida para este componente
                                        required_qty = int(bom_components.get(comp_id, 1))

                                        # Asignar componentes para la cantidad requerida
                                        assigned_qty = 0
                                        for qty_index in range(required_qty):
                                            if temp_components[comp_id] and assigned_qty < required_qty:
                                                component_data = temp_components[comp_id].pop(0)

                                                # # Si el move_raw tiene líneas de movimiento, asignar allí
                                                if move_raw.move_line_ids:
                                                    for move_line in move_raw.move_line_ids:
                                                        if move_line.quantity > assigned_qty:
                                                            if component_data['has_lot']:
                                                                move_line.write({
                                                                    'lot_id': component_data['lot_id'],
                                                                    'qty_done': min(move_line.quantity - assigned_qty, 1)
                                                                })
                                                            else:
                                                                move_line.write({
                                                                    'qty_done': min(move_line.quantity - assigned_qty, 1)
                                                                })
                                                            assigned_qty += 1
                                                            break
                                                else:
                                                    # Crear línea de movimiento si no existe
                                                    env['stock.move.line'].create({
                                                        'move_id': move_raw.id,
                                                        'product_id': comp_id,
                                                        'lot_id': component_data['lot_id'] if component_data['has_lot'] else False,
                                                        'quantity': 1,
                                                        'qty_done': 0,
                                                        'product_uom_id': component_data['uom_id'],
                                                        'location_id': move_raw.location_id.id,
                                                        'location_dest_id': move_raw.location_dest_id.id,
                                                    })
                                                    assigned_qty += 1
                               
                            except Exception as e:
                                error_msg = str(e)
                                self.message_post(body="❌ Error creando orden {}: {}".format(unit_num + 1, error_msg))

                        # Actualizar received_components después de procesar esta BOM
                        for k, v in temp_components.items():
                            received_components[k] = v
                    else:
                        self.message_post(body="⚠️ {}: No se pueden fabricar unidades completas (max_units: {})".format(bom.display_name, max_units))

                if orders_created > 0:
                    self.message_post(body="✅ Automatización completada: {} órdenes de fabricación creadas".format(orders_created))
                else:
                    self.message_post(body="⚠️ No se pudieron crear órdenes de fabricación")
                    self.message_post(body="🔍 Posibles causas: BOMs requieren componentes no recibidos, cantidades insuficientes, o configuración de BOMs incorrecta")   