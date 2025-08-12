from odoo import fields, models

class CustomTemplateAutoDocument(models.Model):
    _name = 'custom.template.auto.document'
    _description = 'Documento auto adjunto de plantilla'
    _rec_name = 'document_id'

    template_id = fields.Many2one('sale.order.template', required=True, ondelete='cascade')
    document_id = fields.Many2one('quotation.document', required=True, ondelete='restrict')
    attach_on_quotation = fields.Boolean(default=True, string="Adjuntar en presupuesto")
    attach_on_order = fields.Boolean(default=False, string="Adjuntar en pedido")
