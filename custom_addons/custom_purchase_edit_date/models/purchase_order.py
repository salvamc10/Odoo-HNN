from odoo import models, fields # type: ignore
"""
Este módulo amplía el modelo de orden de compra para permitir la edición de la fecha de confirmación.
Agrega un nuevo campo llamado 'date_approve' que puede ser editado por el usuario.
"""

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    date_approve = fields.Datetime(
        string="Fecha de confirmación",
        readonly=False
    )
