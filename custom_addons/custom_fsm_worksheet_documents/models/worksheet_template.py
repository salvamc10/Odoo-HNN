from odoo import models, fields, api

class ProjectWorksheetTemplate(models.Model):
    _inherit = 'project.worksheet.template'

    document_folder_id = fields.Many2one(
        'worksheet.document.folder',
        string='Carpeta de Documentos',
        tracking=True
    )
    require_signature = fields.Boolean(
        string='Requiere Firma',
        default=False
    )
    signature_type = fields.Selection([
        ('customer', 'Cliente'),
        ('employee', 'Empleado'),
        ('both', 'Ambos')
    ], string='Tipo de Firma', default='customer')
    signature_fields_ids = fields.One2many(
        'worksheet.signature.field',
        'template_id',
        string='Campos de Firma'
    )
