from odoo import models, fields, api, _
from odoo.exceptions import UserError

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'
    _description = 'Plantilla de Hoja de Trabajo de Reparación'

    def action_edit_template(self):
        """Abre el editor de Studio para personalizar la plantilla"""
        self.ensure_one()
        if not self.model_id:
            raise UserError(_('El modelo técnico aún no se ha creado. Por favor, guarde primero la plantilla.'))

        # Abrir Studio para el modelo dinámico
        return {
            'type': 'ir.actions.client',
            'tag': 'studio.open',
            'params': {
                'model': self.model_id.model,
                'mode': 'edit',
                'action': f'worksheet_{self.id}',
                'studio': True
            },
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        """Sobrescribe create para asegurar la creación del modelo dinámico"""
        if not vals.get('res_model'):
            vals['res_model'] = 'repair.order'
        
        template = super().create(vals)
        
        # Asegurarse de que se crea el modelo dinámico
        if not template.model_id:
            template._compute_model_id()
            
        return template