from odoo import api, fields, models

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    required_quotation_document_ids = fields.Many2many(
        'quotation.document',
        'x_sale_tmpl_req_doc_rel', 'template_id', 'document_id',
        string='Documentos obligatorios',
        help='Se preseleccionarán en el pedido al elegir esta plantilla.',
    )

    @api.constrains('required_quotation_document_ids', 'quotation_document_ids')
    def _check_required_subset(self):
        for rec in self:
            if rec.required_quotation_document_ids - rec.quotation_document_ids:
                raise models.ValidationError(
                    "Los documentos obligatorios deben estar también en 'Documentos' de la plantilla."
                )
