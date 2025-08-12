from odoo import fields, models

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    custom_auto_document_ids = fields.One2many(
        'custom.template.auto.document',
        'template_id',
        string="Documentos automáticos"
    )
