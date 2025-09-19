from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

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
        domain="[('type', '=', 'consu'), ('company_id', 'in', [company_id, False])]", index=True)
    company_id = fields.Many2one('res.company', string='Empresa')
    
    x_supplier_reference = fields.Char(
        string="Referencia del Proveedor",
        help="Código de referencia del proveedor para buscar un producto."
    )

    
    @api.onchange('x_supplier_reference')
    def _onchange_supplier_reference(self):
        """Busca un producto basado en la referencia del proveedor (product_code) y actualiza product_id."""
        _logger.info("Referencia del proveedor: %s, Compañía: %s, Contexto: %s", self.x_supplier_reference, self.company_id.id, self.env.context)
        self.ensure_one()
        if self.x_supplier_reference:
            domain = [('product_code', '=', self.x_supplier_reference)]
            _logger.info("Buscando con dominio: %s", domain)
            supplier_info = self.env['product.supplierinfo'].search(domain, limit=1)
            _logger.info("Supplier info encontrado: %s", supplier_info)
            if supplier_info:
                _logger.info("Supplier info detalles: product_id=%s, product_tmpl_id=%s, company_id=%s", 
                            supplier_info.product_id.id if supplier_info.product_id else False, 
                            supplier_info.product_tmpl_id.id if supplier_info.product_tmpl_id else False,
                            supplier_info.company_id.id if supplier_info.company_id else False)
                if supplier_info.product_id:
                    _logger.info("Asignando product_id directo: %s", supplier_info.product_id.id)
                    self.product_id = supplier_info.product_id.id
                elif supplier_info.product_tmpl_id:
                    product = supplier_info.product_tmpl_id.product_variant_id
                    _logger.info("Asignando desde product_tmpl_id: %s (variante %s)", 
                                supplier_info.product_tmpl_id.id, product.id if product else 'Ninguna')
                    self.product_id = product.id if product else False
                else:
                    _logger.info("No hay product_id ni product_tmpl_id en supplier_info")
                    self.product_id = False
            else:
                _logger.info("No se encontró supplier_info para product_code: %s", self.x_supplier_reference)
                self.product_id = False
                # Depuración adicional: listar todos los product_code disponibles
                all_supplier_codes = self.env['product.supplierinfo'].search([]).mapped('product_code')
                _logger.info("Códigos de proveedor disponibles: %s", all_supplier_codes)
                return {
                    'warning': {
                        'title': _("Advertencia"),
                        'message': _("No se encontró un producto con la referencia del proveedor: %s") % self.x_supplier_reference
                    }
                }
        else:
            self.product_id = False
            

    @api.onchange('refer')
    def _onchange_refer(self):
        """Busca un producto que coincida con refer y actualiza product_id."""
        self.ensure_one()
        if self.refer:
            # Dominio para buscar productos que coincidan con refer
            domain = [
                ('default_code', '=', self.refer),
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
                'product_uom_qty': self.product_uom_qty or 0.0,
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

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe create para actualizar repair.consulta después de crear el producto."""
        products = super(ProductTemplate, self).create(vals_list)

        # Verifica si el contexto incluye un repair_consulta_id
        consulta_id = self._context.get('repair_consulta_id')
        if consulta_id:
            consulta = self.env['repair.consulta'].browse(consulta_id)
            if consulta.exists() and products.product_variant_id:
                consulta.write({'product_id': products.product_variant_id.id})

        return products
