from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RepairWorksheetWizard(models.TransientModel):
    _name = 'repair.worksheet.wizard'
    _description = 'Wizard para rellenar hoja de trabajo de reparación'

    repair_id = fields.Many2one('repair.order', string='Orden de Reparación', required=True)
    template_id = fields.Many2one('repair.worksheet.template', string='Plantilla', required=True)
    partner_id = fields.Many2one(related='repair_id.partner_id', readonly=True)
    worksheet_signature = fields.Binary(string='Firma', required=True)
    notes = fields.Text(string='Notas del Trabajo')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'repair.order' and self.env.context.get('active_id'):
            repair = self.env['repair.order'].browse(self.env.context.get('active_id'))
            res.update({
                'repair_id': repair.id,
                'template_id': repair.worksheet_template_id.id,
            })
        return res

    def action_confirm(self):
        """Confirma y guarda la hoja de trabajo."""
        self.ensure_one()
        if not self.worksheet_signature:
            raise UserError(_('Es necesario firmar la hoja de trabajo.'))

        # Actualizar la orden de reparación con la firma
        self.repair_id.write({
            'worksheet_signature': self.worksheet_signature,
            'worksheet_signature_date': fields.Datetime.now(),
            'worksheet_signed_by': self.repair_id.partner_id.id,
        })

        # Generar el documento PDF
        document = self.repair_id._generate_worksheet_document()
        
        return {
            'type': 'ir.actions.act_window_close'
        }
