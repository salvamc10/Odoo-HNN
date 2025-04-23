from odoo import models, fields # type: ignore

class LotLabelLayout(models.TransientModel):
    _inherit = 'lot.label.layout'

    print_format = fields.Selection(selection_add=[
        ('54x25', '54 x 25')
    ])
