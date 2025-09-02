from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Website(models.Model):
    _inherit = 'website'

    split_by_web_category = fields.Boolean(string='Dividir pedidos por categoría web', default=True)
    recambios_root_public_categ_id = fields.Many2one(
        'product.public.category',
        string='Raíz Recambios (categoría web)',
        help='Toda categoría web descendiente se considera Recambios.'
    )

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    split_done = fields.Boolean(default=False, copy=False)

    # --- helpers ---

    def _product_is_recambio(self, product):
        root = self.website_id.recambios_root_public_categ_id
        if not root:
            return False
        if not product.public_categ_ids:
            return False
        rec_tree_ids = self.env['product.public.category'].search([('id', 'child_of', root.id)]).ids
        return bool(set(product.public_categ_ids.ids) & set(rec_tree_ids))

    def _line_group_key(self, line):
        return 'recambios' if self._product_is_recambio(line.product_id) else 'maquinas'

    def _apply_template_by_group(self, group_key):
        # Usa los nombres de plantilla que has confirmado: "Maquina" y "Recambio"
        name_map = {'maquinas': 'Maquina', 'recambios': 'Recambio'}
        tmpl = self.env['sale.order.template'].search([('name', '=', name_map[group_key])], limit=1)
        if tmpl and self.state in ('draft', 'sent'):
            # Tu write() reasigna la secuencia según la plantilla
            self.write({'sale_order_template_id': tmpl.id})

    def _create_child_order_for_group(self, group_key):
        name_map = {'maquinas': 'Maquina', 'recambios': 'Recambio'}
        tmpl = self.env['sale.order.template'].search([('name', '=', name_map[group_key])], limit=1)
        vals = {
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'pricelist_id': self.pricelist_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'website_id': self.website_id.id,
            'sale_order_template_id': tmpl.id if tmpl else False,
            'origin': self.name,  # << clave
        }
        return self.sudo().create(vals)

    # --- validaciones ---

    @api.constrains('order_line')
    def _check_web_categ_on_published_products(self):
        for order in self:
            if not order.website_id:
                continue
            bad = order.order_line.filtered(
                lambda l: l.product_id.website_published and not l.product_id.public_categ_ids
            )
            if bad:
                raise ValidationError(_("Productos publicados sin categoría web: %s") %
                                      ", ".join(bad.mapped('product_id.display_name')))

    # --- núcleo del split ---

    def split_web_cart_by_category(self):
        self.ensure_one()
        if self.split_done:
            return {'maquinas' if self.order_line and
                    self._line_group_key(self.order_line[0]) == 'maquinas' else 'recambios': self}
    
        groups = {'maquinas': [], 'recambios': []}
        for line in self.order_line:
            groups[self._line_group_key(line)].append(line.id)
    
        # si está desactivado o SOLO hay un grupo, no crear el “otro”
        if (not self.website_id.split_by_web_category) or (not groups['maquinas']) or (not groups['recambios']):
            key = 'recambios' if groups['recambios'] else 'maquinas'
            self._apply_template_by_group(key)
            self.split_done = True
            return {key: self}
    
        # dos grupos: mantener self para máquinas y crear hijo para recambios
        orders = {'maquinas': self}
        self._apply_template_by_group('maquinas')
        orders['recambios'] = self._create_child_order_for_group('recambios')
    
        # mover solo las líneas de recambios al hijo
        self.env['sale.order.line'].browse(groups['recambios']).write({'order_id': orders['recambios'].id})
    
        for so in orders.values():
            so.split_done = True
        return orders
