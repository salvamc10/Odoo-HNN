from odoo import models, fields, api

class WorksheetDocumentFolder(models.Model):
    _name = 'worksheet.document.folder'
    _description = 'Worksheet Document Folder'
    _inherit = ['mail.thread']

    name = fields.Char(string='Nombre', required=True)
    document_folder_id = fields.Many2one(
        'documents.folder', 
        string='Carpeta de Documentos',
        required=True,
        tracking=True
    )
    template_ids = fields.One2many(
        'project.worksheet.template',
        'document_folder_id',
        string='Plantillas'
    )
    active = fields.Boolean(default=True)
    description = fields.Text(string='Descripción')
    tags_ids = fields.Many2many(
        'documents.tag',
        string='Etiquetas de Documento',
        domain="[('folder_id', '=', document_folder_id)]"
    )
