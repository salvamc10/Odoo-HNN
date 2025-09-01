from odoo import models, fields, api

class FSMReport(models.Model):
    _inherit = "industry.fsm.report"

    repair_id = fields.Many2one("repair.order", string="Reparación")