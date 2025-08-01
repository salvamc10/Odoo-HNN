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
        # Buscar la orden de compra asociada a esta recepción
        purchase_orders = self.move_ids.mapped('purchase_line_id.order_id')
        if not purchase_orders:
            self.message_post(body="⚠️ No se pudo determinar la orden de compra asociada a esta recepción.")
            return

        purchase_order = purchase_orders[0]  # Tomar la primera orden de compra (normalmente solo hay una)
        
        # Buscar todas las recepciones asociadas a la misma orden de compra
        related_pickings = self.env['stock.picking'].search([
            ('picking_type_id.code', '=', 'incoming'),
            ('state', '=', 'done'),
            '|',  # OR condition
            ('origin', '=', purchase_order.name),
            ('purchase_id', '=', purchase_order.id),
        ])

        self.message_post(body="🔄 Iniciando automatización de órdenes de fabricación para la orden de compra '{}'...".format(purchase_order.name))
        
        # Recopilar TODOS los componentes recibidos en todas las recepciones
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
            self.message_post(body="❌ No se encontraron componentes recibidos para la orden de compra '{}'.".format(purchase_order.name))
            return

        # Mostrar componentes recibidos
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

        # Buscar órdenes de fabricación existentes para esta orden de compra
        existing_mos = self.env['mrp.production'].search([('origin', '=', purchase_order.name)])
        used_components = {}
        
        # Rastrear componentes ya utilizados en órdenes de fabricación existentes
        for mo in existing_mos:
            for move_raw in mo.move_raw_ids:
                comp_id = move_raw.product_id.id
                if comp_id not in used_components:
                    used_components[comp_id] = 0
                used_components[comp_id] += int(move_raw.product_qty)

        # Calcular componentes disponibles restando los ya utilizados
        available_components = {}
        for product_id, components in received_components.items():
            available_qty = max(0, len(components) - used_components.get(product_id, 0))
            if available_qty > 0:
                available_components[product_id] = components[:int(available_qty)]
                
        if not available_components:
            self.message_post(body="⚠️ No hay componentes disponibles para nuevas órdenes de fabricación (todos ya utilizados).")
            return

        # Buscar BOMs que contengan alguno de los componentes disponibles
        matching_boms = []
        for product_id in available_components.keys():
            bom_lines = env['mrp.bom.line'].search([('product_id', '=', product_id)])
            for bom_line in bom_lines:
                if bom_line.bom_id not in matching_boms:
                    matching_boms.append(bom_line.bom_id)

        self.message_post(body="🔍 BOMs encontradas que usan estos componentes: {}".format(len(matching_boms)))

        if not matching_boms:
            self.message_post(body="⚠️ No se encontraron BOMs que utilicen los componentes disponibles.")
            return

        orders_created = 0
        mrp_model = env['mrp.production']

        # Para cada BOM encontrada, verificar si podemos fabricar productos
        for bom in matching_boms:
            self.message_post(body="📋 Evaluando BOM: {}".format(bom.display_name))

            # Mapear todos los componentes de esta BOM
            bom_components = {}  # {product_id: cantidad_requerida}
            missing_components = []
            bom_available_components = {}

            for bom_line in bom.bom_line_ids:
                comp_id = bom_line.product_id.id
                bom_components[comp_id] = bom_line.product_qty
                if comp_id in available_components:
                    bom_available_components[comp_id] = bom_line.product_qty
                else:
                    missing_components.append(bom_line.product_id.name)

            # Si faltan componentes requeridos, saltar esta BOM
            if missing_components:
                missing_text = ', '.join(missing_components[:3])
                if len(missing_components) > 3:
                    missing_text += '...'
                self.message_post(body="⚠️ {}: Saltando BOM - faltan componentes: {}".format(bom.display_name, missing_text))
                continue

            # Mostrar componentes disponibles
            available_list = []
            for comp_id in bom_available_components.keys():
                comp_name = env['product.product'].browse(comp_id).name
                available_list.append(comp_name)
            available_text = ', '.join(available_list[:3])
            if len(available_list) > 3:
                available_text += '...'
            self.message_post(body="✅ {}: Todos los componentes disponibles: {}".format(bom.display_name, available_text))

            # Calcular cuántas unidades podemos fabricar
            max_units = 999999
            for comp_id, required_qty in bom_components.items():
                available_qty = len(available_components.get(comp_id, []))
                if required_qty > 0:
                    possible_units = int(available_qty / required_qty)
                    if possible_units < max_units:
                        max_units = possible_units

            if max_units == 0 or max_units == 999999:
                self.message_post(body="⚠️ {}: No se pueden fabricar unidades completas (max_units: {})".format(bom.display_name, max_units))
                continue

            # Crear órdenes de fabricación
            self.message_post(body="🏭 {}: Creando {} órdenes...".format(bom.display_name, max_units))

            # Hacer una copia de available_components para esta BOM
            temp_components = {}
            for k, v in available_components.items():
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
                        'origin': purchase_order.name,  # Usar el nombre de la orden de compra como origen
                    })

                    mo.write({
                        'state': 'draft',
                        'product_qty': 1,
                    })
                    orders_created += 1

                    # Asignar números de serie/lotes a los componentes
                    for move_raw in mo.move_raw_ids:
                        comp_id = move_raw.product_id.id
                        if comp_id in temp_components and temp_components[comp_id]:
                            required_qty = int(bom_components.get(comp_id, 1))
                            assigned_qty = 0
                            for qty_index in range(required_qty):
                                if temp_components[comp_id] and assigned_qty < required_qty:
                                    component_data = temp_components[comp_id].pop(0)
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

            # Actualizar available_components después de procesar esta BOM
            for k, v in temp_components.items():
                available_components[k] = v

        if orders_created > 0:
            self.message_post(body="✅ Automatización completada: {} órdenes de fabricación creadas para la orden de compra '{}'.".format(
                orders_created, purchase_order.name))
        else:
            self.message_post(body="⚠️ No se crearon órdenes de fabricación para la orden de compra '{}'. Posibles causas: componentes insuficientes, BOMs incompletas, o productos no relacionados con BOMs.".format(
                purchase_order.name))