from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    # No se sobrescribe el campo, solo se deja preparado por si se quiere extender en el futuro