from uuid import uuid4
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Website(models.Model):
    _inherit = 'website'

    split_by_web_category = fields.Boolean(string='Dividir pedidos por categoría web', default=True)
    recambios_root_public_categ_id = fields.Many2one('product.public.category', string='Raíz Recambios (categoría web)')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    split_done = fields.Boolean(default=False, copy=False)
    split_group_uid = fields.Char(index=True, copy=False)

    def _product_is_recambio(self, product):
        root = self.website_id.recambios_root_public_categ_id
        if not root or not product.public_categ_ids:
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

    def _create_child_order_for_group(self, group_key):
        vals = {
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'pricelist_id': self.pricelist_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'website_id': self.website_id.id,
            'origin': self.name,
            'split_group_uid': self.split_group_uid,
            'carrier_id': getattr(self, 'carrier_id', False) and self.carrier_id.id or False,
            'sale_order_template_id': False,
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
        countable = self.order_line.filtered(self._is_countable_product_line)
        
        if not countable:
            if not self.split_group_uid:
                self.split_group_uid = str(uuid4())
            self.split_done = True
            self._auto_assign_quotation_template()
            return {'maquinas': self}
        
        groups = {'maquinas': [], 'recambios': []}
        for line in countable:
            groups[self._line_group_key(line)].append(line.id)
        
        if not self.split_group_uid:
            self.split_group_uid = str(uuid4())
        
        if self.split_done and (not groups['maquinas'] or not groups['recambios']):
            key = 'recambios' if groups['recambios'] else 'maquinas'
            self._auto_assign_quotation_template()
            return {key: self}
        
        if (not self.website_id.split_by_web_category) or (not groups['maquinas']) or (not groups['recambios']):
            key = 'recambios' if groups['recambios'] else 'maquinas'
            self.split_done = True
            self._auto_assign_quotation_template()
            return {key: self}
        
        orders = {'maquinas': self}
        orders['recambios'] = self._create_child_order_for_group('recambios')
        self.env['sale.order.line'].browse(groups['recambios']).write({'order_id': orders['recambios'].id})
        
        for so in orders.values():
            so.split_done = True
            if hasattr(so, '_update_delivery_price') and getattr(so, 'carrier_id', False):
                try:
                    so._update_delivery_price()
                except Exception:
                    pass
        
        for so in orders.values():
            so._auto_assign_quotation_template()
        
        return orders
    
    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        
        if 'order_line' in vals:
            for order in self:
                if order.website_id:
                    order._auto_assign_quotation_template()
        
        return result
    
    def _auto_assign_quotation_template(self):
        self.ensure_one()
        
        self.env.invalidate_all()
        
        if self.sale_order_template_id:
            return
        
        countable = self.order_line.filtered(self._is_countable_product_line)
        if not countable:
            return
        
        has_recambios = False
        has_maquinas = False
        
        for line in countable:
            if self._product_is_recambio(line.product_id):
                has_recambios = True
            else:
                has_maquinas = True
        
        template_name = None
        if has_recambios and not has_maquinas:
            template_name = 'Recambio'
        elif has_maquinas and not has_recambios:
            template_name = 'Maquina'
        
        if template_name:
            template = self.env['sale.order.template'].sudo().search([('name', '=', template_name)], limit=1)
            if template:
                self.env.cr.execute(
                    "UPDATE sale_order SET sale_order_template_id = %s WHERE id = %s",
                    (template.id, self.id)
                )
                self.env.invalidate_all()
