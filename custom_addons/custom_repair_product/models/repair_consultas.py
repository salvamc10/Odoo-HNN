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
        domain="[('type', '=', 'consu')]", index=True, required=True)

    @api.onchange('consulta_text', 'refer')
    def _onchange_consulta_text_or_refer(self):
        """Busca un producto que coincida con consulta_text o refer y actualiza product_id."""
        self.ensure_one()
        if self.consulta_text or self.refer:
            # Dominio para buscar productos que coincidan con consulta_text o refer
            domain = [
                '|',
                ('name', 'ilike', self.consulta_text or ''),
                ('default_code', 'ilike', self.refer or ''),
                ('type', '=', 'consu')
            ]
            # Busca el primer producto que coincida
            product = self.env['product.product'].search(domain, limit=1)
            # Si se encuentra un producto, asigna su ID; si no, deja product_id en blanco
            self.product_id = product.id if product else False
        else:
            # Si ambos campos están vacíos, limpia product_id
            self.product_id = False