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

    x_studio_direccion = fields.Many2one(
        comodel_name='res.partner',
        string='Dirección de Contacto',
    )

    display_address = fields.Char(
        string='Dirección de Contacto Mostrada',
        compute='_compute_display_address',
        readonly=True,
    )

    x_numero_consultas = fields.Float(
        string="Numero de consultas pendientes",
        compute='_compute_x_numero_consultas',
        store=False,  
    )

    x_forecast_availibility = fields.Float(            
        string="Numero de recambios pte servir",
        compute='_compute_forecast_availability',
        store=False,  
    )
    
    @api.depends('consulta_ids', 'consulta_ids.product_id')
    def _compute_x_numero_consultas(self):
        for record in self:
            # Contar consultas pendientes: aquellas donde product_id no está establecido
            record.x_numero_consultas = len(record.consulta_ids.filtered(lambda c: not c.product_id))

    @api.depends('move_ids', 'move_ids.forecast_availability', 'move_ids.product_uom_qty', 'move_ids.state', 'move_ids.product_id', 'move_ids.picking_id', 'move_ids.picking_id.state')
    def _compute_forecast_availability(self):
        for record in self:
            # Filtrar movimientos relevantes (no completados ni cancelados)
            moves = record.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            count = 0
            for move in moves:
                if not move.product_id or move.product_uom_qty <= 0:
                    continue
                # Contar si no está disponible (forecast_availability < product_uom_qty)
                if move.forecast_availability < move.product_uom_qty:
                    count += 1
                    continue
                # Contar si hay movimientos de entrada pendientes (compra confirmada no validada)
                incoming_moves = self.env['stock.move'].search([
                    ('product_id', '=', move.product_id.id),
                    ('state', 'in', ('confirmed', 'assigned', 'partially_available')),
                    ('picking_type_id.code', '=', 'incoming'),
                    ('id', '!=', move.id),
                    ('picking_id.state', '!=', 'done'),  # Solo compras no validadas
                ])
                if incoming_moves:
                    count += 1
            record.x_forecast_availibility = count
            
    @api.depends('x_studio_direccion')
    def _compute_display_address(self):
        """Calcula la dirección completa basada en x_studio_direccion."""
        for record in self:
            if record.x_studio_direccion:
                address = record.x_studio_direccion
                address_lines = [
                    address.street or '',
                    address.city or '',
                    address.zip or '',
                    address.state_id.name or '',
                    address.country_id.name or ''
                ]
                record.display_address = ', '.join(filter(None, address_lines))
            else:
                record.display_address = ''

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Limpia el campo x_studio_direccion si cambia el partner_id."""
        if self.partner_id:
            self.x_studio_direccion = False  
            return {
                'domain': {
                    'x_studio_direccion': [
                        '|',
                        ('id', '=', self.partner_id.id),
                        '&',
                        ('parent_id', '=', self.partner_id.id),
                        ('type', '=', 'other')
                    ]
                }
            }
        return {
            'domain': {
                'x_studio_direccion': []
            }
        }

    @api.onchange('consulta_ids')
    def _onchange_consulta_ids(self):
        """Guarda el formulario cuando se modifican las consultas."""

        if not self._origin or not self.consulta_ids:
            return
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

    def action_create_sale_order(self):
        """Override to add stock.move products to sale.order.option for type 'Recambios'."""
        if any(repair.sale_order_id for repair in self):
            concerned_ro = self.filtered('sale_order_id')
            ref_str = "\n".join(concerned_ro.mapped('name'))
            raise UserError(
                _(
                    "You cannot create a quotation for a repair order that is already linked to an existing sale order.\nConcerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                ),
            )

        if any(not repair.partner_id for repair in self):
            concerned_ro = self.filtered(lambda ro: not ro.partner_id)
            ref_str = "\n".join(concerned_ro.mapped('name'))
            raise UserError(
                _(
                    "You need to define a customer for a repair order in order to create an associated quotation.\nConcerned repair order(s):\n%(ref_str)s",
                    ref_str=ref_str,
                ),
            )
        
        vals_list = [{
            "company_id": r.company_id.id,
            "partner_id": r.partner_id.id,
            "warehouse_id": r.picking_type_id.warehouse_id.id if r.picking_type_id.warehouse_id else False,
            "repair_order_ids": [(6, 0, [r.id])],
        } for r in self]
        
        sale_orders = self.env['sale.order'].create(vals_list)
        sale_orders_by_repair = dict(zip(self.ids, sale_orders))

        for repair in self:
            sale_order = sale_orders_by_repair[repair.id]
            sale_order.ensure_one()
    
            if (repair.type or '').lower() == 'recambios':
                stock_moves = repair.move_ids.filtered(lambda m: m.state != 'cancel') if hasattr(repair, 'move_ids') else self.env['stock.move'].search([('repair_id', '=', repair.id), ('state', '!=', 'cancel')])
    
                if 'sale.order.option' in self.env:
                    Option = self.env['sale.order.option']
                    for move in stock_moves:
                        Option.create({
                            'order_id': sale_order.id,
                            'product_id': move.product_id.id,
                            'name': move.product_id.display_name or move.product_id.name,
                            'quantity': move.product_uom_qty,
                            'uom_id': move.product_uom.id,
                            'price_unit': move.product_id.lst_price,
                        })
            else:
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

        model_name = template.model_id.model
        if not model_name:
            raise UserError(_("La plantilla seleccionada no tiene un modelo generado. Es posible que esté dañada. Por favor crea o selecciona otra."))
    
        if model_name not in self.env:
            raise UserError(_("El modelo dinámico '%s' no está disponible. Puede que se haya eliminado o no se haya generado correctamente.") % model_name)

        Model = self.env[model_name]

        if not self.env.user.has_group('base.group_user'):
            raise UserError(_("No tienes permisos para acceder a los registros de esta plantilla. Contacta a tu administrador."))

        link_field = f"x_{self._name.replace('.', '_')}_id"

        rec = Model.search([(link_field, "=", self.id)], limit=1)

        if not rec:
            vals = {link_field: self.id}
            if "x_name" in Model._fields:
                vals["x_name"] = self.name or ""
            rec = Model.create(vals)

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
        return "custom_repair_product.group_repair_manager"

    def _get_repair_order_user_group(self):
        return "repair.group_repair_user"

    def action_open_repair_worksheet(self):
        """Abre (o crea) la hoja de trabajo usando la plantilla asignada."""
        self.ensure_one()
        if not self.x_repair_worksheet_template_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "worksheet.template",
                "view_mode": "form",
                "target": "new",
                "context": {"default_res_model":"repair.order"},
            }
        return self.x_repair_worksheet_template_id.action_open_worksheet(self)
