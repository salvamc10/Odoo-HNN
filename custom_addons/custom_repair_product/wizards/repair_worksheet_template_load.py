from odoo import fields, models

class RepairWorksheetTemplateLoad(models.TransientModel):
    _name = 'repair.worksheet.template.load.wizard'
    _description = 'Load the worksheet template for repair orders'

    repair_order_id = fields.Many2one('repair.order', "Repair Order", required=True, default=lambda self: self._context.get('active_id'))

    def action_open_template(self):
        return self.repair_order_id.action_view_worksheet() 