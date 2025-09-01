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
    )
        
    x_repair_worksheet_template_id = fields.Many2one(
        "worksheet.template",
        string="Plantilla de trabajo",
        domain=[("res_model", "=", "repair.order")],
        help="Plantilla de worksheet creada con Studio para órdenes de reparación."
    )


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
            # if updates:
            #     self.write({'consulta_ids': updates})

               
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

    
    def action_view_worksheet(self):
        """
        Abre (o crea si no existe) la instancia de worksheet correspondiente
        a esta reparación, usando la plantilla seleccionada.
        En v18 las instancias se guardan en el modelo dinámico de la plantilla
        (template.model_id.model) y se vinculan con x_<res_model>_id.
        """
        self.ensure_one()
        template = self.x_repair_worksheet_template_id
        if not template:
            raise UserError(_("Selecciona una plantilla de trabajo."))

        # Modelo dinámico generado por la plantilla (ej.: x_worksheet_fsm_123)
        model_name = template.model_id.model
        if not model_name:
            raise UserError(_("La plantilla seleccionada no tiene un modelo generado. Es posible que esté dañada. Por favor crea o selecciona otra."))
    
        if model_name not in self.env:
            raise UserError(_("El modelo dinámico '%s' no está disponible. Puede que se haya eliminado o no se haya generado correctamente.") % model_name)

        Model = self.env[model_name]

        # Nombre del campo de enlace (convención de worksheets/Studio)
        link_field = f"x_{self._name.replace('.', '_')}_id"   # -> x_repair_order_id

        # Buscar si ya existe un worksheet para esta reparación
        rec = Model.search([(link_field, "=", self.id)], limit=1)

        # Si no existe, crearlo con mínimos defaults
        if not rec:
            vals = {link_field: self.id}
            # Si la plantilla tiene un campo 'x_name', úsalo
            if "x_name" in Model._fields:
                vals["x_name"] = self.name or ""
            rec = Model.create(vals)

        # Abrir el formulario del registro dinámico
        return {
            "type": "ir.actions.act_window",
            "res_model": model_name,
            "view_mode": "form",
            "res_id": rec.id,
            "target": "current",
            "context": {
                f"default_{link_field}": self.id,
                "from_repair_order": True,
                "studio": True,
                "resModel": model_name,
            },
        }

    def _get_repair_order_manager_group(self):
        # usa el tuyo o el nativo de repair
        return "custom_repair_product.group_repair_manager"  # ó "repair.group_repair_manager"

    def _get_repair_order_user_group(self):
        # grupo con permisos de usuario sobre las worksheets de repair
        return "repair.group_repair_user"

    def action_open_repair_worksheet(self):
        """Abre (o crea) la hoja de trabajo usando la plantilla asignada."""
        self.ensure_one()
        if not self.x_repair_worksheet_template_id:
            # Si no hay plantilla, abre el formulario de selección
            return {
                "type": "ir.actions.act_window",
                "res_model": "worksheet.template",
                "view_mode": "form",
                "target": "new",
                "context": {"default_res_model":"repair.order"},
            }
        # Método estándar de worksheet que genera el registro dinámico
        return self.x_repair_worksheet_template_id.action_open_worksheet(self)
    