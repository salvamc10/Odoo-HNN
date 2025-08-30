from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'

    res_model = fields.Char('Host Model', default='repair.order', help="The model that is using this template")

    @api.depends('name')
    def _compute_model_id(self):
        IrModel = self.env['ir.model']
        for template in self:
            model_name = 'x_repair_worksheet_%s' % template.id
            template.model_id = IrModel.search([('model', '=', model_name)], limit=1)
            if not template.model_id and template.name:
                model_vals = {
                    'name': _('Hoja de Trabajo: %s') % template.name,
                    'model': model_name,
                    'inherited_model_ids': [(6, 0, [self.env.ref('custom_repair_product.model_repair_worksheet').id])],
                    'state': 'manual',
                    'transient': False,
                }
                template.model_id = IrModel.sudo().create(model_vals)
                if not self.env['ir.ui.view'].search([('model', '=', model_name), ('type', '=', 'form')]):
                    self.env['ir.ui.view'].sudo().create({
                        'name': _('Vista Form por Defecto: %s') % template.name,
                        'model': model_name,
                        'type': 'form',
                        'arch': '''
                            <form string="%s">
                                <sheet>
                                    <group>
                                        <field name="notes"/>
                                        <field name="worksheet_signature" widget="signature"/>
                                    </group>
                                </sheet>
                            </form>
                        ''' % template.name,
                    })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('res_model'):
                vals['res_model'] = 'repair.order'
        templates = super().create(vals_list)
        for template in templates:
            if not template.model_id:
                template._compute_model_id()
        return templates

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