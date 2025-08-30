# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo import _
import logging

_logger = logging.getLogger(__name__)

class RepairOrder(models.Model):
    _inherit = 'repair.order'
    
    consulta_ids = fields.One2many('repair.consulta', 'repair_order_id', string="Consultas")
    
    type = fields.Selection(
        string="Tipo",
        selection=[('Reparación', 'Reparación'), ('Recambios', 'Recambios')],
        ondelete={'Reparación': 'cascade', 'Recambios': 'cascade'}
    )
    
    allow_worksheets = fields.Boolean(
        string="Permitir Hojas de Trabajo",
        default=True,
        help="Habilita el uso de hojas de trabajo en esta orden de reparación"
    )

    worksheet_template_id = fields.Many2one(
        'worksheet.template', 
        string="Plantilla de Hoja de Trabajo",
        tracking=True,
        domain="[('res_model', '=', 'repair.order'), ('active', '=', True)]",
        context={
            'default_res_model': 'repair.order',
            'default_name': 'Hoja de Reparación'
        },
        help="Seleccione una plantilla para personalizar la hoja de trabajo"
    )
    
    worksheet_count = fields.Integer(compute='_compute_worksheet_count')

    def _compute_worksheet_count(self):
        for record in self:
            if record.worksheet_template_id and record.worksheet_template_id.model_id:
                model = record.worksheet_template_id.model_id.model
                record.worksheet_count = self.env[model].search_count([('repair_id', '=', record.id)])
            else:
                record.worksheet_count = 0
    

    def _get_worksheet_record(self):
            """Obtiene o crea el registro de hoja de trabajo dinámico."""
            self.ensure_one()
            if not self.worksheet_template_id:
                raise UserError(_('Seleccione una plantilla primero.'))
            model = self.worksheet_template_id.model_id.model
            worksheet = self.env[model].search([('repair_id', '=', self.id)], limit=1)
            if not worksheet:
                worksheet = self.env[model].create({
                    'repair_id': self.id,
                    'template_id': self.worksheet_template_id.id,
                })
            return worksheet
    
    @api.onchange('consulta_ids')
    def _onchange_consulta_ids(self):
        """Guarda el formulario cuando se modifican las consultas."""
        if not self._origin or not self.consulta_ids:
            return
            
        # Solo procesar consultas que ya existen en la base de datos
        existing_consultas = self.consulta_ids.filtered('id')
        if existing_consultas:
            updates = []
            for consulta in existing_consultas:
                if consulta._origin:
                    updates.append((1, consulta.id, {
                        'consulta_text': consulta.consulta_text,
                        'refer': consulta.refer,
                        'product_uom_qty': consulta.product_uom_qty,
                        'picked': consulta.picked,
                        'product_id': consulta.product_id.id if consulta.product_id else False,
                    }))
            if updates:
                self.write({'consulta_ids': updates})

    def action_worksheet_sign(self):
        """Abre wizard de firma, que actualiza el worksheet dinámico."""
        self.ensure_one()
        worksheet = self._get_worksheet_record()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Firmar Hoja de Trabajo'),
            'res_model': 'repair.worksheet.signature.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_repair_id': self.id, 'default_worksheet_model': worksheet._name, 'default_worksheet_id': worksheet.id},
        }

    def _generate_worksheet_document(self):
        """Genera informe PDF renderizando la vista form del worksheet."""
        self.ensure_one()
        worksheet = self._get_worksheet_record()
        return self.env.ref('custom_repair_product.action_report_repair_worksheet')._render_qweb_pdf([worksheet.id])[0]  # Ajusta action

    def action_validate(self):
        """Sobreescribe el método de validación."""
        return super().action_validate()

    def action_fsm_worksheet(self):
        """Abre la hoja de trabajo dinámica."""
        self.ensure_one()
        worksheet = self._get_worksheet_record()
        return {
            'type': 'ir.actions.act_window',
            'res_model': worksheet._name,
            'view_mode': 'form',
            'res_id': worksheet.id,
            'target': 'current',  # O 'new' para ventana emergente
            'context': {'form_view_initial_mode': 'edit'},
        }

            
    def action_create_sale_order(self):
        """Override to add stock.move products to sale.order.option for type 'Recambios'."""
        # Check if any repair order is already linked to a sale order
        if any(repair.sale_order_id for repair in self):
            concerned_ro = self.filtered('sale_order_id')
            ref_str = "\n".join(ro.name for ro in concerned_ro)
            raise UserError(
                _(
                    "You cannot create a quotation for a repair order that is already linked to an existing sale order.\nConcerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                ),
            )
            
        # Check if partner_id is set
        if any(not repair.partner_id for repair in self):
            concerned_ro = self.filtered(lambda ro: not ro.partner_id)
            ref_str = "\n".join(ro.name for ro in concerned_ro)
            raise UserError(
                _(
                    "You need to define a customer for a repair order in order to create an associated quotation.\nConcerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                ),
            )
        
        sale_order_values_list = []
        for repair in self:
            sale_order_values_list.append({
                "company_id": repair.company_id.id,
                "partner_id": repair.partner_id.id,
                "warehouse_id": repair.picking_type_id.warehouse_id.id if repair.picking_type_id.warehouse_id else False,
                "repair_order_ids": [(6, 0, [repair.id])],
            })
        
        # Create sale orders
        sale_orders = self.env['sale.order'].create(sale_order_values_list)
        
        # Handle stock.move products based on type
        for repair in self:
            if repair.type == 'Recambios':
                # For 'Recambios', add stock.move products to sale.order.option
                stock_moves = self.env['stock.move'].search([
                    ('repair_id', '=', repair.id),
                    ('state', '!=', 'cancel')
                ])
                sale_order = sale_orders.filtered(lambda so: repair.id in so.repair_order_ids.ids)
                if sale_order:
                    for move in stock_moves:
                        if hasattr(self.env, 'sale.order.option'):
                            self.env['sale.order.option'].create({
                                'order_id': sale_order.id,
                                'product_id': move.product_id.id,
                                'name': move.product_id.name,
                                'quantity': move.product_uom_qty,
                                'uom_id': move.product_uom.id,
                                'price_unit': move.product_id.lst_price,
                            })
            else:
                # For other types, use the default behavior to add to sale.order.line
                if hasattr(repair, 'move_ids'):
                    repair.move_ids._create_repair_sale_order_line()
        
        return self.action_view_sale_order()
    
    def action_load_worksheet_template(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'worksheet.template.load.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_repair_id': self.id},
        }