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
                ('default_code', '=', self.refer or ''),
                ('type', '=', 'consu')
            ]
            # Busca el primer producto que coincida
            product = self.env['product.product'].search(domain, limit=1)
            # Si se encuentra un producto, asigna su ID; si no, deja product_id en blanco
            self.product_id = product.id if product else False
        else:
            # Si ambos campos están vacíos, limpia product_id
            self.product_id = False