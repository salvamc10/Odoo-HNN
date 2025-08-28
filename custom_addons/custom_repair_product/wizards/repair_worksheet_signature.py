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
        """Procesa la firma, la guarda en la orden de reparación y genera el documento PDF."""
        self.ensure_one()
        if not self.signature:
            raise UserError('Se requiere una firma para continuar.')
            
        if not self.repair_id.worksheet_template_id:
            raise UserError('No hay una plantilla de hoja de trabajo configurada.')

        values = {
            'worksheet_signature': self.signature,
            'worksheet_signature_date': fields.Datetime.now(),
            'worksheet_signed_by': self.signed_by.id,
        }

        # Generar el documento PDF si hay una plantilla de informe configurada
        if self.repair_id.worksheet_template_id.report_view_id:
            report_template = self.repair_id.worksheet_template_id.report_view_id
            report_name = f"Hoja de trabajo - {self.repair_id.name}"
            
            # Generar PDF
            pdf_content = report_template._render_qweb_pdf(self.repair_id.id)[0]
            
            # Crear el documento en el sistema de documentos
            document = self.env['documents.document'].create({
                'name': report_name,
                'datas': pdf_content,
                'folder_id': self.repair_id.worksheet_template_id.document_folder_id.id,
                'res_model': 'repair.order',
                'res_id': self.repair_id.id,
                'mimetype': 'application/pdf',
            })
            
            values['worksheet_document_id'] = document.id

        # Actualizar la orden de reparación
        self.repair_id.write(values)

        return {'type': 'ir.actions.act_window_close'}
