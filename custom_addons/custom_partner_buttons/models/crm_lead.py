from odoo import models, fields, api
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_lead_origin_id = fields.Many2one(
        'crm.lead',
        string='Lead origen',
        help='Lead del que se generó esta oportunidad'
    )

    @api.constrains('partner_id', 'type', 'active')
    def _check_unique_lead_per_partner(self):
        for record in self:
            # Solo aplicar si es un lead (no oportunidad) y tiene partner
            if record.partner_id and record.type == 'lead' and record.active:
                existing = self.search([
                    ('partner_id', '=', record.partner_id.id),
                    ('id', '!=', record.id),
                    ('type', '=', 'lead'),
                    ('active', '=', True)
                ], limit=1)
                if existing:
                    raise UserError("Ya existe un lead activo para este cliente.")

    def action_create_direct_opportunity(self):
        self.ensure_one()
        if self.type != 'lead':
            raise UserError("Esta acción solo se puede usar desde un lead.")
    
        new_opportunity = self.copy({
            'type': 'opportunity',
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'x_lead_origin_id': self.id,
        })
    
        return {
            'name': 'Oportunidad',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': new_opportunity.id,
            'target': 'current',
        }
