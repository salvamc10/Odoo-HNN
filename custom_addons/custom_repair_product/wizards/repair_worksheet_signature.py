from odoo import models, fields, api
from odoo.exceptions import UserError

class RepairWorksheetSignatureWizard(models.TransientModel):
    _name = 'repair.worksheet.signature.wizard'
    _description = 'Asistente de Firma de Hoja de Trabajo'

    repair_id = fields.Many2one('repair.order', required=True)
    signature = fields.Binary(string='Firma', required=True)
    signed_by = fields.Many2one('res.partner', string='Firmado por')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_repair_id'):
            repair = self.env['repair.order'].browse(self.env.context['default_repair_id'])
            if repair.exists():
                res['signed_by'] = repair.partner_id.id
        return res

    def action_sign_worksheet(self):
        """Procesa la firma y la guarda en la orden de reparación."""
        self.ensure_one()
        if not self.signature:
            raise UserError('Se requiere una firma para continuar.')

        self.repair_id.write({
            'worksheet_signature': self.signature,
            'worksheet_signature_date': fields.Datetime.now(),
            'worksheet_signed_by': self.signed_by.id,
        })

        return {'type': 'ir.actions.act_window_close'}
