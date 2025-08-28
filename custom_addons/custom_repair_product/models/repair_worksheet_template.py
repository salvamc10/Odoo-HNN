from odoo import models, fields, api

class RepairWorksheetTemplate(models.Model):
    _name = 'repair.worksheet.template'
    _description = 'Plantilla de Hoja de Trabajo de Reparación'
    _inherit = ['mail.thread']

    name = fields.Char('Nombre', required=True, translate=True)
    description = fields.Html('Descripción', translate=True)
    active = fields.Boolean(default=True)
    document_folder_id = fields.Many2one(
        'documents.folder',
        string='Carpeta de Documentos',
        tracking=True
    )
    worksheet_count = fields.Integer(compute='_compute_worksheet_count', string='Número de Hojas de Trabajo')
    report_view_id = fields.Many2one('ir.ui.view', string='Vista del Informe', domain=[('type', '=', 'qweb')])
    require_signature = fields.Boolean(
        string='Requiere Firma',
        default=False
    )
    signature_type = fields.Selection([
        ('customer', 'Cliente'),
        ('employee', 'Empleado'),
        ('both', 'Ambos')
    ], string='Tipo de Firma', default='customer')

    worksheet_template_sequence = fields.Integer(string='Sequence', default=10)
