from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    # Clase preparada para futuras extensiones sin sobrescribir el campo original.
