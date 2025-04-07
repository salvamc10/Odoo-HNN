from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    # No se sobrescribe el campo original. Esta clase está preparada para extensiones futuras.
