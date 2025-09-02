from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from uuid import uuid4

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
    split_group_uid = fields.Char(index=True, copy=False)

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

    def _is_countable_product_line(self, line):
        if getattr(line, 'display_type', False):
            return False
        if not line.product_id:
            return False
        if getattr(line, 'is_delivery', False):
            return False
        if getattr(line, 'is_downpayment', False):
            return False
        if getattr(line, 'is_reward', False):
            return False
        return True

    def _apply_template_by_group(self, group_key):
        name_map = {'maquinas': 'Maquina', 'recambios': 'Recambio'}
        tmpl = self.env['sale.order.template'].search([('name', '=', name_map[group_key])], limit=1)
        if tmpl and self.state in ('draft', 'sent'):
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
            'origin': self.name,
            'split_group_uid': self.split_group_uid,  # clave común
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

        countable = self.order_line.filtered(self._is_countable_product_line)
        if not countable:
            # No hay productos reales que dividir
            if not self.split_group_uid:
                self.split_group_uid = str(uuid4())
            self.split_done = True
            return {'maquinas': self}

        groups = {'maquinas': [], 'recambios': []}
        for line in countable:
            groups[self._line_group_key(line)].append(line.id)

        # asegurar UID de grupo
        if not self.split_group_uid:
            self.split_group_uid = str(uuid4())

        # ya estaba split_done y ahora es homogéneo -> nada que hacer
        if self.split_done and (not groups['maquinas'] or not groups['recambios']):
            key = 'recambios' if groups['recambios'] else 'maquinas'
            return {key: self}

        # si está desactivado o SOLO hay un grupo, marcar y salir
        if (not self.website_id.split_by_web_category) or (not groups['maquinas']) or (not groups['recambios']):
            key = 'recambios' if groups['recambios'] else 'maquinas'
            self._apply_template_by_group(key)
            self.split_done = True
            return {key: self}

        # hay dos grupos: mantener self para máquinas y crear hijo para recambios
        orders = {'maquinas': self}
        self._apply_template_by_group('maquinas')
        orders['recambios'] = self._create_child_order_for_group('recambios')

        # mover SOLO las líneas de recambios al hijo
        self.env['sale.order.line'].browse(groups['recambios']).write({'order_id': orders['recambios'].id})

        for so in orders.values():
            so.split_done = True
        return orders
