from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RepairWorksheetWizard(models.TransientModel):
    _name = 'repair.worksheet.wizard'
    _description = 'Wizard para rellenar hoja de trabajo de reparación'

    repair_id = fields.Many2one('repair.order', string='Orden de Reparación')
    template_id = fields.Many2one('repair.worksheet.template', string='Plantilla')
    partner_id = fields.Many2one(related='repair_id.partner_id', readonly=True)
    worksheet_signature = fields.Binary(string='Firma')
    notes = fields.Text(string='Notas del Trabajo')
    
    @api.model
    def default_get(self, fields_list):
        """Valores por defecto del wizard"""
        defaults = super().default_get(fields_list)
        
        # Obtener repair_id del contexto
        repair_id = self._context.get('default_repair_id')
        if repair_id:
            repair = self.env['repair.order'].browse(repair_id)
            if repair.exists():
                defaults['repair_id'] = repair.id
                if repair.worksheet_template_id:
                    defaults['template_id'] = repair.worksheet_template_id.id
                    
        return defaults

    def action_confirm(self):
        """Confirma la hoja de trabajo y guarda la información"""
        self.ensure_one()
        
        if not self.repair_id:
            raise UserError(_('No se ha especificado una orden de reparación.'))

        # Actualizar la orden de reparación con la información de la hoja de trabajo
        values = {}
        
        if self.worksheet_signature:
            values.update({
                'worksheet_signature': self.worksheet_signature,
                'worksheet_signature_date': fields.Datetime.now(),
                'worksheet_signed_by': self.partner_id.id,
            })

        if values:
            self.repair_id.write(values)

        # Generar el documento si está configurado
        if (self.repair_id.worksheet_template_id and 
            self.repair_id.worksheet_template_id.document_folder_id):
            self.repair_id._generate_worksheet_document()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }