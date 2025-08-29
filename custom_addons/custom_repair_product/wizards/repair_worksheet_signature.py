from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RepairWorksheetSignatureWizard(models.TransientModel):
    _name = 'repair.worksheet.signature.wizard'
    _description = 'Asistente de Firma para Hoja de Trabajo'

    repair_id = fields.Many2one(
        'repair.order', 
        string='Orden de Reparación', 
        required=True
    )
    partner_id = fields.Many2one(
        related='repair_id.partner_id', 
        string='Cliente', 
        readonly=True
    )
    worksheet_signature = fields.Binary(
        string='Firma', 
        required=True
    )

    @api.model
    def default_get(self, fields_list):
        """Valores por defecto del wizard"""
        defaults = super().default_get(fields_list)
        
        # Obtener repair_id del contexto
        repair_id = self._context.get('default_repair_id')
        if repair_id:
            defaults['repair_id'] = repair_id
            
        return defaults

    def action_sign(self):
        """Procesa la firma de la hoja de trabajo"""
        self.ensure_one()
        
        if not self.repair_id:
            raise UserError(_('No se ha especificado una orden de reparación.'))
            
        if not self.worksheet_signature:
            raise UserError(_('Debe proporcionar una firma.'))

        # Guardar la firma en la orden de reparación
        self.repair_id.write({
            'worksheet_signature': self.worksheet_signature,
            'worksheet_signature_date': fields.Datetime.now(),
            'worksheet_signed_by': self.partner_id.id,
        })

        # Generar el documento firmado
        self.repair_id._generate_worksheet_document()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }