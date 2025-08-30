from odoo import models, fields, api, _
from odoo.exceptions import UserError

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'
    _description = 'Plantilla de Hoja de Trabajo de Reparación'

    @api.depends('name')
    def _compute_model_id(self):
        IrModel = self.env['ir.model']
        for template in self:
            model_name = 'x_repair_worksheet_%s' % template.id
            template.model_id = IrModel.search([('model', '=', model_name)], limit=1)
            if not template.model_id and template.name:
                # Crear modelo dinámico si no existe
                model_vals = {
                    'name': _('Hoja de Trabajo: %s') % template.name,
                    'model': model_name,
                    'inherited_model_ids': [(6, 0, [self.env.ref('custom_repair_product.model_repair_worksheet').id])],  # Hereda del base (ajusta ref si es XML ID)
                    'state': 'manual',
                    'transient': False,
                }
                template.model_id = IrModel.sudo().create(model_vals)
                # Crear vista form básica si no existe
                if not self.env['ir.ui.view'].search([('model', '=', model_name), ('type', '=', 'form')]):
                    self.env['ir.ui.view'].sudo().create({
                        'name': _('Vista Form por Defecto: %s') % template.name,
                        'model': model_name,
                        'type': 'form',
                        'arch': '<form string="%s"><sheet><group><field name="notes"/></group></sheet></form>' % template.name,
                    })
                    
    def action_edit_template(self):
        self.ensure_one()
        if not self.model_id:
            self._compute_model_id()
            if not self.model_id:
                raise UserError(_('No se pudo crear el modelo dinámico.'))
        return {
            'type': 'ir.actions.client',
            'tag': 'studio',
            'params': {
                'model': self.model_id.model,
                'view_type': 'form',
                'studio': True,
            },
        }

    @api.model
    def create(self, vals):
        template = super().create(vals)
        template._compute_model_id()  # Asegura creación inmediata
        return template