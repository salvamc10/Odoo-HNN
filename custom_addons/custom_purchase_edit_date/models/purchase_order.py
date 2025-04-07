from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    date_approve = fields.Datetime(
        string="Fecha de confirmación",
        readonly=False
    )
