from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    invoice_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Documento a adjuntar en factura',
        domain="[('res_model', '=', 'product.template')]"
    )
