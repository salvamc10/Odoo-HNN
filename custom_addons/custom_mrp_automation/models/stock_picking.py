# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_mrp_automation_done = fields.Boolean(string="MRP Automatizado", default=False, help="Evita múltiples ejecuciones de la automatización.")

    def button_validate(self):
        res = super().button_validate()
        for record in self:
            if record.picking_type_id.code == 'incoming' and record.state == 'done' and not record.x_mrp_automation_done:
                try:
                    record._run_mrp_automation()
                    record.x_mrp_automation_done = True
                except Exception as e:
                    _logger.error("Error en automatización MRP: %s", str(e))
                    record.message_post(body="❌ Error en automatización de MRP: {}".format(str(e)))
        return res

    def _run_mrp_automation(self):
        self.message_post(body="🔄 Iniciando automatización de órdenes de fabricación...")
        received_components, summary_msg = self._collect_received_components()
        self.message_post(body=summary_msg)

        if not received_components:
            self.message_post(body="❌ No se encontraron componentes recibidos")
            return

        matching_boms = self._find_boms_for_components(received_components)
        self.message_post(body="🔍 BOMs encontradas que usan estos componentes: {}".format(len(matching_boms)))

        if not matching_boms:
            self.message_post(body="⚠️ No se encontraron BOMs que utilicen los componentes recibidos")
            return

        orders_created = self._evaluate_and_create_mos(matching_boms, received_components)

        if orders_created > 0:
            self.message_post(body="✅ Automatización completada: {} órdenes de fabricación creadas".format(orders_created))
        else:
            self.message_post(body="⚠️ No se pudieron crear órdenes de fabricación")
            self.message_post(body="🔍 Posibles causas: BOMs requieren componentes no recibidos, cantidades insuficientes, o configuración incorrecta")

    def _collect_received_components(self):
        received_components = {}
        total_components = 0
        components_with_lots = 0
        components_without_lots = 0

        for line in self.move_line_ids:
            if line.qty_done > 0:
                total_components += 1
                product_id = line.product_id.id
                if product_id not in received_components:
                    received_components[product_id] = []

                for _ in range(int(line.qty_done)):
                    received_components[product_id].append({
                        'lot_id': line.lot_id.id if line.lot_id else False,
                        'product_id': product_id,
                        'uom_id': line.product_uom_id.id,
                        'has_lot': bool(line.lot_id),
                    })

                if line.lot_id:
                    components_with_lots += 1
                else:
                    components_without_lots += 1

        # Generar resumen
        msg = "✅ Componentes recibidos: {} tipos diferentes<br/>".format(len(received_components))
        msg += "📊 Total líneas: {} ({} con lotes, {} sin lotes)<br/>".format(total_components, components_with_lots, components_without_lots)

        for prod_id, components in received_components.items():
            product_name = self.env['product.product'].browse(prod_id).name
            with_lots = sum(1 for c in components if c['has_lot'])
            without_lots = sum(1 for c in components if not c['has_lot'])
            msg += "• {}: {} unidades".format(product_name, len(components))
            if with_lots and without_lots:
                msg += " ({} con lote, {} sin lote)<br/>".format(with_lots, without_lots)
            elif with_lots:
                msg += " (con lotes)<br/>"
            else:
                msg += " (sin lotes)<br/>"

        return received_components, msg

    def _find_boms_for_components(self, received_components):
        bom_ids = set()
        bom_lines = self.env['mrp.bom.line'].search([('product_id', 'in', list(received_components.keys()))])
        for line in bom_lines:
            bom_ids.add(line.bom_id.id)
        return self.env['mrp.bom'].browse(list(bom_ids))

    def _evaluate_and_create_mos(self, boms, received_components):
        env = self.env
        mrp_model = env['mrp.production']
        orders_created = 0

        for bom in boms:
            self.message_post(body="📋 Evaluando BOM: {}".format(bom.display_name))
            bom_components = {line.product_id.id: line.product_qty for line in bom.bom_line_ids}
            available = {pid: received_components[pid] for pid in bom_components if pid in received_components}
            missing = [line.product_id.name for line in bom.bom_line_ids if line.product_id.id not in received_components]

            if not available:
                self.message_post(body="⚠️ {}: No contiene ninguno de los componentes recibidos".format(bom.display_name))
                continue

            if missing:
                msg = ', '.join(missing[:3]) + ('...' if len(missing) > 3 else '')
                self.message_post(body="ℹ️ {}: Componentes faltantes: {}".format(bom.display_name, msg))
                self.message_post(body="⚠️ {}: Saltando BOM - faltan componentes requeridos".format(bom.display_name))
                continue  # eliminar este continue si quieres permitir parciales

            available_names = ', '.join(self.env['product.product'].browse(pid).name for pid in available.keys()[:3])
            if len(available) > 3:
                available_names += '...'
            self.message_post(body="✅ {}: Componentes disponibles: {}".format(bom.display_name, available_names))

            max_units = min(int(len(received_components[pid]) / qty) for pid, qty in bom_components.items() if pid in received_components and qty > 0)
            if not max_units:
                self.message_post(body="⚠️ {}: No se pueden fabricar unidades completas".format(bom.display_name))
                continue

            self.message_post(body="🏭 {}: Creando {} órdenes...".format(bom.display_name, max_units))
            temp_components = {pid: comps[:] for pid, comps in received_components.items()}

            for i in range(max_units):
                try:
                    product = bom.product_tmpl_id.product_variant_id
                    mo = mrp_model.create({
                        'product_id': product.id,
                        'product_qty': 1,
                        'product_uom_id': product.uom_id.id,
                        'bom_id': bom.id,
                        'origin': self.name,
                    })
                    mo.action_confirm()
                    mo.action_assign()
                    orders_created += 1
                    self._assign_serials_to_moves(mo, bom_components, temp_components)
                    self.message_post(body="✅ Orden {} creada: {}".format(i + 1, mo.name))
                except Exception as e:
                    self.message_post(body="❌ Error creando orden {}: {}".format(i + 1, str(e)))

            for k, v in temp_components.items():
                received_components[k] = v

        return orders_created

    def _assign_serials_to_moves(self, mo, bom_components, temp_components):
        for move_raw in mo.move_raw_ids:
            comp_id = move_raw.product_id.id
            if comp_id not in temp_components or not temp_components[comp_id]:
                continue
            required_qty = int(bom_components.get(comp_id, 1))
            assigned = 0
            for _ in range(required_qty):
                if not temp_components[comp_id] or assigned >= required_qty:
                    break
                data = temp_components[comp_id].pop(0)
                if move_raw.move_line_ids:
                    for ml in move_raw.move_line_ids:
                        if ml.quantity > assigned:
                            ml.write({
                                'lot_id': data['lot_id'] if data['has_lot'] else False,
                                'qty_done': min(ml.quantity - assigned, 1)
                            })
                            assigned += 1
                            break
                else:
                    mo.env['stock.move.line'].create({
                        'move_id': move_raw.id,
                        'product_id': comp_id,
                        'lot_id': data['lot_id'] if data['has_lot'] else False,
                        'quantity': 1,
                        'qty_done': 1,
                        'product_uom_id': data['uom_id'],
                        'location_id': move_raw.location_id.id,
                        'location_dest_id': move_raw.location_dest_id.id,
                    })
                    assigned += 1
