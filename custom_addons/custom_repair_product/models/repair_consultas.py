from odoo import models, fields, api

class RepairConsulta(models.Model):
    _name = 'repair.consulta'
    _description = 'Consulta técnica'

    repair_order_id = fields.Many2one(
        'repair.order',
        string="Orden de reparación",
        ondelete='cascade'
    )
    consulta_text = fields.Text(string="Producto a consultar")
    refer = fields.Char(string="Referencia")
    product_uom_qty = fields.Float(string="Cantidad")
    picked = fields.Boolean(string="Usado")
    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        domain="[('type', '=', 'consu')]", index=True)
    

    @api.onchange('refer')
    def _onchange_refer(self):
        """Busca un producto que coincida con refer y actualiza product_id."""
        self.ensure_one()
        if self.refer:
            # Dominio para buscar productos que coincidan con refer
            domain = [
                ('default_code', 'ilike', self.refer),
                ('type', '=', 'consu')
            ]
            # Busca el primer producto que coincida
            product = self.env['product.product'].search(domain, limit=1)
            # Si se encuentra un producto, asigna su ID; si no, deja product_id en blanco
            self.product_id = product.id if product else False
            
        else:
            # Si ambos campos están vacíos, limpia product_id
            self.product_id = False
            
    def action_create_product(self):
        """Devuelve una acción para crear un nuevo producto y actualiza product_id."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_type': 'consu',
                'default_default_code': self.refer or '',
                'default_name': self.consulta_text or '',
                'repair_consulta_id': self.id,
            },
        }

    def action_add_to_repair_lines(self):
        """Añade el producto consultado a las líneas de reparación."""
        self.ensure_one()
        if not self.product_id:
            return
            
        repair_order = self.repair_order_id
        if repair_order:
            # Crear el stock.move
            self.env['stock.move'].create({
                'repair_id': repair_order.id,
                'product_id': self.product_id.id,
                'product_uom_qty': self.product_uom_qty or 1.0,
                'product_uom': self.product_id.uom_id.id,
                'location_id': repair_order.location_id.id,
                'location_dest_id': repair_order.location_dest_id.id,
                'repair_line_type': 'add',
                'name': self.product_id.name,
                'state': 'draft',
            })
            # Eliminar la consulta después de añadirla
            self.unlink()

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        """Sobrescribe create para actualizar repair.consulta después de crear el producto."""
        product = super().create(vals)
        
        # Verifica si el contexto incluye un repair_consulta_id
        consulta_id = self._context.get('repair_consulta_id')
        if consulta_id:
            consulta = self.env['repair.consulta'].browse(consulta_id)
            if consulta.exists() and product.product_variant_id:
                consulta.write({'product_id': product.product_variant_id.id})
                
        return product