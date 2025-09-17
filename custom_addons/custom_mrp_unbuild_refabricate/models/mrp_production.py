from odoo import models, api, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_unbuild(self):
        """
        Desmonta una orden de fabricación (MO) y crea una nueva MO de refabricación,
        asignando los mismos lotes/series a los componentes rastreados.
        """
        for production in self:
            self._check_state_done(production)
            ctx = self._get_unbuild_context(production)
            self._create_and_validate_unbuild(production, ctx)
            bom_refab = self._find_refabrication_bom(production)
            new_production = self._create_new_refab_mo(production, bom_refab)
            new_production.action_confirm()  
            self._assign_tracked_lots_to_new_mo(production, new_production)
            new_production.action_assign()  # Asignar/reservar stock en la nueva MO
        return True

    def _check_state_done(self, production):
        """Verifica que la orden esté en estado 'done'."""
        if production.state != 'done':
            raise UserError(_(f"La orden {production.name} no está en estado 'Hecho'."))

    def _get_unbuild_context(self, production):
        """Prepara el contexto necesario para el wizard de unbuild."""
        ctx = dict(self.env.context)
        ctx.update({
            'active_model': 'mrp.production',
            'active_id': production.id,
            'default_mo_id': production.id,  
        })
        return ctx

    def _create_and_validate_unbuild(self, production, ctx):
        """Crea y valida el registro de unbuild."""
        unbuild = self.env['mrp.unbuild'].with_context(ctx).create({
            'product_id': production.product_id.id,
            'bom_id': production.bom_id.id,
            'lot_id': production.lot_producing_id.id if production.lot_producing_id else False,
            'location_id': production.location_dest_id.id,
            'company_id': production.company_id.id,
        })
        unbuild.action_validate()

    def _find_refabrication_bom(self, production):
        """Busca la BOM de refabricación con distintivo '-R'."""
        bom_refab = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', production.product_tmpl_id.id),
            ('code', 'ilike', '-R')
        ], limit=1)
        if not bom_refab:
            raise UserError(_(f"No se encontró una BOM de refabricación con distintivo '-R' para el producto {production.product_id.name}."))
        return bom_refab

    def _create_new_refab_mo(self, production, bom_refab):
        """Crea una nueva MO con la BOM de refabricación y el mismo lote/serie."""
        new_production_vals = {
            'product_id': production.product_id.id,
            'product_uom_id': production.product_uom_id.id,
            'bom_id': bom_refab.id,
            'product_qty': production.qty_produced, 
            'lot_producing_id': production.lot_producing_id.id if production.lot_producing_id else False,
            'company_id': production.company_id.id,
            'location_src_id': production.location_src_id.id,
            'location_dest_id': production.location_dest_id.id,
        }
        return self.env['mrp.production'].create(new_production_vals)

    def _assign_tracked_lots_to_new_mo(self, original_production, new_production):
        """
        Empareja componentes rastreados: asigna los mismos lotes/series de la MO original
        a los movimientos de la nueva MO.
        """
        original_raw_moves = original_production.move_raw_ids
        for new_raw_move in new_production.move_raw_ids:
            # Encontrar movimiento original correspondiente por producto
            matching_original_moves = original_raw_moves.filtered(lambda m: m.product_id == new_raw_move.product_id)
            if matching_original_moves:
                for original_move in matching_original_moves:
                    for orig_line in original_move.move_line_ids:
                        if new_raw_move.product_id.tracking != 'none': 
                            new_line_vals = {
                                'move_id': new_raw_move.id,
                                'product_id': new_raw_move.product_id.id,
                                'qty_done': min(orig_line.qty_done, new_raw_move.product_uom_qty),
                                'lot_id': orig_line.lot_id.id if orig_line.lot_id else False,
                                'package_id': orig_line.package_id.id if orig_line.package_id else False,
                                'result_package_id': orig_line.result_package_id.id if orig_line.result_package_id else False,
                                'location_id': new_raw_move.location_id.id,
                                'location_dest_id': new_raw_move.location_dest_id.id,
                            }
                            self.env['stock.move.line'].create(new_line_vals)