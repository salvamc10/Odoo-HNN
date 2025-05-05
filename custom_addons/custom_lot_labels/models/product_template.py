from odoo import models, fields # type: ignore

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_ubicacion_temporal = fields.Char(string="Ubicación temporal")
