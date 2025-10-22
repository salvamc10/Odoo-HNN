from odoo import api, models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _action_done(self):
        # Llamar al método original primero para validar la recepción
        res = super(StockPicking, self)._action_done()
        
        # Procesar solo recepciones validadas para compañía 2
        for picking in self:
            if (picking.picking_type_id.code != 'incoming' or 
                picking.company_id.id != 2 or 
                not picking.move_line_ids):
                continue
                
            # Recopilar números de serie/lote únicos y mapear a cuentas
            lot_to_account = {}  # {lot_name: account_id}
            lot_names = set()
            for move_line in picking.move_line_ids:
                if move_line.lot_id and move_line.qty_done > 0:
                    lot_name = move_line.lot_id.name
                    lot_names.add(lot_name)
            
            if not lot_names:
                continue
            
            # Obtener el plan analítico predefinido para la compañía 2
            analytic_plan = self.env['account.analytic.plan'].search([
                ('company_id', '=', 2)
            ], limit=1)
            if not analytic_plan:
                raise UserError(_('No se encontró un plan analítico predefinido para la compañía 2.'))
            
            # Crear cuentas analíticas únicas por lote/serie (de HU1)
            for lot_name in lot_names:
                # Verificar si ya existe (por código único)
                existing_account = self.env['account.analytic.account'].search([
                    ('code', '=', lot_name),
                    ('company_id', '=', 2)
                ], limit=1)
                if not existing_account:
                    # Crear la nueva cuenta
                    new_account = self.env['account.analytic.account'].create({
                        'name': f'RCT-{lot_name}',
                        'code': lot_name,
                        'plan_id': analytic_plan.id,
                        'optional': True,
                        'company_id': 2,
                        'parent_id': False,  # Cuenta raíz
                        'active': True,
                    })
                    lot_to_account[lot_name] = new_account.id
                    self.env['ir.logging'].create({
                        'name': 'Cuenta analítica creada',
                        'type': 'server',
                        'level': 'INFO',
                        'message': f'Cuenta analítica creada para {lot_name}: {new_account.name} (ID: {new_account.id}).',
                        'path': 'stock_picking._action_done',
                        'func': '_action_done',
                        'line': '1',
                    })
                else:
                    lot_to_account[lot_name] = existing_account.id
                    self.env['ir.logging'].create({
                        'name': 'Cuenta analítica ya existe',
                        'type': 'server',
                        'level': 'INFO',
                        'message': f'La cuenta analítica para {lot_name} ya existe (ID: {existing_account.id}).',
                        'path': 'stock_picking._action_done',
                        'func': '_action_done',
                        'line': '1',
                    })
            
            # Nueva lógica: Distribución analítica automática en purchase.order.line (HU2)
            if not picking.purchase_id:
                self.env['ir.logging'].create({
                    'name': 'Sin PO asociada',
                    'type': 'server',
                    'level': 'WARNING',
                    'message': f'No se encontró orden de compra para el picking {picking.id}.',
                    'path': 'stock_picking._action_done',
                    'func': '_action_done',
                    'line': '1',
                })
                continue
            
            # Agrupar qty_done por purchase_line_id y lot_name para distribución equitativa
            distribution_data = {}  # {purchase_line_id: {lot_name: qty_total_por_lote}}
            for move_line in picking.move_line_ids:
                if move_line.lot_id and move_line.qty_done > 0 and move_line.move_id.purchase_line_id:
                    purchase_line_id = move_line.move_id.purchase_line_id.id
                    lot_name = move_line.lot_id.name
                    if purchase_line_id not in distribution_data:
                        distribution_data[purchase_line_id] = {}
                    if lot_name not in distribution_data[purchase_line_id]:
                        distribution_data[purchase_line_id][lot_name] = 0.0
                    distribution_data[purchase_line_id][lot_name] += move_line.qty_done
            
            # Para cada purchase_line, calcular y asignar distribución
            for purchase_line_id, lot_qty_map in distribution_data.items():
                purchase_line = self.env['purchase.order.line'].browse(purchase_line_id)
                total_qty = sum(lot_qty_map.values())  # Total unidades en esta línea
                if total_qty == 0:
                    continue
                
                # Calcular porcentajes: (qty_por_lote / total_qty) * 100 para cada cuenta
                analytic_dist = {}  # {account_id: porcentaje/100.0}
                for lot_name, qty_lote in lot_qty_map.items():
                    account_id = lot_to_account.get(lot_name)
                    if account_id:
                        porcentaje = (qty_lote / total_qty) * 100.0
                        analytic_dist[account_id] = porcentaje / 100.0  # Formato JSON: fracción
                
                if analytic_dist:
                    # Actualizar o setear analytic_distribution (mergea si existe)
                    current_dist = purchase_line.analytic_distribution or {}
                    current_dist.update(analytic_dist)  # Sobrescribe solo las nuevas
                    purchase_line.write({'analytic_distribution': current_dist})
                    
                    self.env['ir.logging'].create({
                        'name': 'Distribución analítica actualizada',
                        'type': 'server',
                        'level': 'INFO',
                        'message': f'Distribución aplicada en PO línea {purchase_line_id}: {analytic_dist} (total qty: {total_qty}).',
                        'path': 'stock_picking._action_done',
                        'func': '_action_done',
                        'line': '1',
                    })
        
        return res