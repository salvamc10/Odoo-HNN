from odoo import fields, models

class SaleOrderTemplateDocument(models.Model):
    _inherit = 'sale.order.template.document'

    attach_on_quotation = fields.Boolean(
        string='Adjuntar en presupuesto',
        help='Si está activo, se adjuntará siempre al crear el presupuesto.'
    )
    attach_on_order = fields.Boolean(
        string='Adjuntar en pedido',
        help='Si está activo, se adjuntará siempre al confirmar el pedido.'
    )
