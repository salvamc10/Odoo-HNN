from odoo import models, fields, api
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    worksheet_signature = fields.Binary(string='Firma')
    worksheet_signature_date = fields.Datetime(string='Fecha de Firma')
    worksheet_signed_by = fields.Many2one(
        'res.partner',
        string='Firmado por'
    )
    worksheet_document_id = fields.Many2one(
        'documents.document',
        string='Documento de Hoja de Trabajo',
        copy=False
    )

    def action_fsm_worksheet_signature(self):
        """Abre el asistente de firma para la hoja de trabajo."""
        self.ensure_one()
        if not self.worksheet_template_id:
            raise UserError('Esta tarea no tiene una plantilla de hoja de trabajo asignada.')
        if not self.worksheet_template_id.require_signature:
            raise UserError('Esta plantilla no requiere firma.')
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Firmar Hoja de Trabajo',
            'res_model': 'worksheet.signature.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_id': self.id}
        }

    def _generate_worksheet_document(self):
        """Genera el documento PDF y lo guarda en la carpeta configurada."""
        self.ensure_one()
        if not self.worksheet_template_id or not self.worksheet_template_id.document_folder_id:
            return

        folder = self.worksheet_template_id.document_folder_id
        # Generar PDF
        report_template = self.worksheet_template_id.report_view_id
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report_template.id, [self.id]
        )

        # Crear documento
        document = self.env['documents.document'].create({
            'name': f"Hoja de trabajo - {self.name}",
            'folder_id': folder.document_folder_id.id,
            'partner_id': self.partner_id.id,
            'owner_id': self.user_id.id,
            'datas': pdf_content,
            'mimetype': 'application/pdf',
            'tag_ids': [(6, 0, folder.tags_ids.ids)]
        })

        self.worksheet_document_id = document.id
        return document

    def action_fsm_validate(self):
        """Sobreescribe el método de validación para incluir la generación del documento."""
        res = super().action_fsm_validate()
        if self.worksheet_template_id and self.worksheet_template_id.document_folder_id:
            self._generate_worksheet_document()
        return res
