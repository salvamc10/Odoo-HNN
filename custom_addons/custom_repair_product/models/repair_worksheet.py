from odoo import api, fields, models, _

class RepairWorksheet(models.AbstractModel):
    _name = 'repair.worksheet'
    _description = 'Repair Worksheet'
    _auto = False  # No se crea tabla en la base de datos
    
    repair_id = fields.Many2one('repair.order', string="Orden de Reparación", ondelete='cascade')
    template_id = fields.Many2one('worksheet.template', string="Plantilla", ondelete='cascade')
    notes = fields.Text(string="Notas")
    worksheet_signature = fields.Binary(string='Firma')
    worksheet_signature_date = fields.Datetime(string='Fecha de Firma')
    worksheet_signed_by = fields.Many2one('res.partner', string='Firmado por', ondelete='set null')

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        """Permite renderizado dinámico para informes."""
        arch, view = super()._get_view(view_id, view_type, **options)
        
        return arch, view