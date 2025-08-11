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
            'origin': self.origin or False,
        }
        return self.sudo().create(vals)

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

    def split_web_cart_by_category(self):
        self.ensure_one()
        if self.split_done:
            return {'maquinas': self}

        groups = {'maquinas': [], 'recambios': []}
        for line in self.order_line:
            groups[self._line_group_key(line)].append(line.id)

        if not groups['recambios'] or not self.website_id.split_by_web_category:
            self._apply_template_by_group('maquinas')
            self.split_done = True
            self._amount_all()
            return {'maquinas': self}

        orders = {}
        if groups['maquinas']:
            orders['maquinas'] = self
            self._apply_template_by_group('maquinas')
        else:
            orders['recambios'] = self
            self._apply_template_by_group('recambios')

        other = 'recambios' if 'maquinas' in orders else 'maquinas'
        orders[other] = orders.get(other) or self._create_child_order_for_group(other)

        for grp, line_ids in groups.items():
            if not line_ids:
                continue
            target = orders[grp]
            self.env['sale.order.line'].browse(line_ids).write({'order_id': target.id})

        for so in orders.values():
            so._amount_all()
            so.split_done = True

        return orders
