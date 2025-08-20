# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    consulta_text = fields.Char(string='Consulta')

