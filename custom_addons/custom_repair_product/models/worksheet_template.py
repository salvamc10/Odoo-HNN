from odoo import models, fields, api, _
from odoo.exceptions import UserError

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'
    _description = 'Plantilla de Hoja de Trabajo de Reparación'

    def action_edit_template(self):
        """Abre el editor de Studio para personalizar la plantilla"""
        self.ensure_one()
        if not self.model_id:
            # Crear el modelo si no existe
            model_name = f'x_repair_worksheet_{self.id}'
            self.env['ir.model'].sudo().create({
                'name': self.name,
                'model': model_name,
                'state': 'manual',
                'transient': False,
            })
            # Actualizar el modelo_id
            self._compute_model_id()

        # Abrir Studio para el modelo dinámico
        return {
            'type': 'ir.actions.client',
            'tag': 'studio.edit_view',
            'params': {
                'model': self.model_id.model,
                'mode': 'edit',
                'view_type': 'form',
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