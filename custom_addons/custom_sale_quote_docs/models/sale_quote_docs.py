from odoo import api, fields, models

class CustomSaleQuoteDoc(models.Model):
    _name = "custom.sale.quote.doc"
    _description = "Doc en plantilla de presupuesto"

    template_id = fields.Many2one("sale.order.template", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    attachment_id = fields.Many2one("ir.attachment", required=True)
    default_checked = fields.Boolean(string="Marcado por defecto", default=True)
    sequence = fields.Integer(default=10)

class CustomSaleOrderDoc(models.Model):
    _name = "custom.sale.order.doc"
    _description = "Doc seleccionado en pedido"

    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    attachment_id = fields.Many2one("ir.attachment", required=True)
    checked = fields.Boolean(string="Enviar", default=True)
    sequence = fields.Integer(default=10)
    source_line_id = fields.Many2one("custom.sale.quote.doc")

class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    quote_doc_ids = fields.One2many("custom.sale.quote.doc", "template_id", string="Documentos")

class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_doc_ids = fields.One2many("custom.sale.order.doc", "order_id", string="Documentos a enviar")

    @api.onchange("sale_order_template_id")
    def _onchange_sale_order_template_id_docs(self):
        """Cuando el usuario elige plantilla, precargar docs."""
        for order in self:
            order.order_doc_ids = [(5, 0, 0)]
            if order.sale_order_template_id:
                vals_list = []
                for line in order.sale_order_template_id.quote_doc_ids.sorted("sequence"):
                    vals_list.append((0, 0, {
                        "name": line.name,
                        "attachment_id": line.attachment_id.id,
                        "checked": bool(line.default_checked),
                        "sequence": line.sequence,
                        "source_line_id": line.id,
                    }))
                order.order_doc_ids = vals_list

    def action_quotation_send(self):
        """Inyectar adjuntos marcados al wizard de correo."""
        self.ensure_one()
        res = super().action_quotation_send()
        attach_ids = self.order_doc_ids.filtered("checked").mapped("attachment_id").ids
        if res and isinstance(res, dict):
            ctx = dict(res.get("context", {}))
            existing = ctx.get("default_attachment_ids") or []
            # Quitar duplicados
            ctx["default_attachment_ids"] = list(set(existing + attach_ids))
            res["context"] = ctx
        return res
