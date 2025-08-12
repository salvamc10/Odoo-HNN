from odoo import api, fields, models

class CustomQuoteTemplateDoc(models.Model):
    _name = "custom.quote.template.doc"
    _description = "Documentos por defecto de plantilla de presupuesto"
    _order = "sequence, id"

    template_id = fields.Many2one(
        "sale.order.template", required=True, ondelete="cascade"
    )
    document_id = fields.Many2one(
        "quotation.document", required=True, ondelete="restrict"
    )
    required = fields.Boolean(string="Obligatorio", default=False)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        (
            "template_document_uniq",
            "unique(template_id, document_id)",
            "El documento ya está asignado a esta plantilla.",
        )
    ]


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    custom_template_doc_ids = fields.One2many(
        "custom.quote.template.doc",
        "template_id",
        string="Documentos por defecto",
    )

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        # Semilla opcional: si la plantilla ya tenía documentos M2M, los copia como no obligatorios
        for rec in recs:
            if rec.quotation_document_ids:
                existing = rec.custom_template_doc_ids.mapped("document_id")
                to_add = rec.quotation_document_ids - existing
                if to_add:
                    rec.custom_template_doc_ids = [
                        (
                            0,
                            0,
                            {
                                "document_id": d.id,
                                "required": False,
                                "sequence": getattr(d, "sequence", 10),
                            },
                        )
                        for d in to_add
                    ]
        return recs
