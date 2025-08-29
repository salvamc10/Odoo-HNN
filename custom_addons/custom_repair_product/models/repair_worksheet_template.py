from odoo import models, fields, api

class RepairWorksheetTemplate(models.Model):
    _name = 'repair.worksheet.template'
    _description = 'Plantilla de Hoja de Trabajo de Reparación'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char('Nombre', translate=True, required=True)
    description = fields.Html('Descripción', translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    
    document_folder_id = fields.Many2one(
        'documents.folder',
        string='Carpeta de Documentos',
        tracking=True
    )
    worksheet_count = fields.Integer(
        compute='_compute_worksheet_count', 
        string='Número de Hojas de Trabajo'
    )
    report_view_id = fields.Many2one(
        'ir.ui.view', 
        string='Vista del Informe', 
        domain=[('type', '=', 'qweb')]
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

    worksheet_template_sequence = fields.Integer(string='Sequence', default=10)

    @api.depends('name')
    def _compute_worksheet_count(self):
        """Calcula el número de hojas de trabajo que usan esta plantilla"""
        for record in self:
            # Contar repair.order que usan esta plantilla
            record.worksheet_count = self.env['repair.order'].search_count([
                ('worksheet_template_id', '=', record.id)
            ])
    