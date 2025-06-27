from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_opportunity_partner_id = fields.Many2one(
        'res.partner',
        string='Contacto (solo oportunidades)',
        compute='_compute_custom_partner_links',
        store=True
    )

    x_lead_partner_id = fields.Many2one(
        'res.partner',
        string='Contacto (solo leads)',
        compute='_compute_custom_partner_links',
        store=True
    )

    @api.depends('partner_id', 'type')
    def _compute_custom_partner_links(self):
        for lead in self:
            if lead.type == 'opportunity':
                lead.x_opportunity_partner_id = lead.partner_id
                lead.x_lead_partner_id = False
            elif lead.type == 'lead':
                lead.x_lead_partner_id = lead.partner_id
                lead.x_opportunity_partner_id = False
            else:
                lead.x_lead_partner_id = False
                lead.x_opportunity_partner_id = False


class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_activity_done_date = fields.Date(
        string='Última actividad realizada',
        compute='_compute_last_activity_done_date',
        store=True
    )

    x_pending_lead_activity_count = fields.Integer(
        string="Actividades pendientes (Leads)",
        compute="_compute_pending_activity_counts",
        store=False
    )
    
    x_pending_opportunity_activity_count = fields.Integer(
        string="Actividades pendientes (Oportunidades)",
        compute="_compute_pending_activity_counts",
        store=False
    )
    
    x_pending_activity_count = fields.Integer(
        string="Actividades pendientes (Total)",
        compute="_compute_pending_activity_counts",
        store=False
    )

    x_opportunity_ids = fields.One2many(
        'crm.lead',
        'x_opportunity_partner_id',
        string='Oportunidades del contacto'
    )

    x_lead_ids = fields.One2many(
        'crm.lead',
        'x_lead_partner_id',
        string='Leads del contacto'
    )

    x_opportunity_count = fields.Integer(
        string='Número de oportunidades',
        compute='_compute_custom_lead_counts',
        store=True
    )

    x_lead_count = fields.Integer(
        string='Número de leads',
        compute='_compute_custom_lead_counts',
        store=True
    )

    @api.depends('x_opportunity_ids', 'x_lead_ids')
    def _compute_custom_lead_counts(self):
        for partner in self:
            partner.x_opportunity_count = len(partner.x_opportunity_ids)
            partner.x_lead_count = len(partner.x_lead_ids)

    @api.depends('x_opportunity_ids.message_ids', 'x_lead_ids.message_ids')
    def _compute_last_activity_done_date(self):
        for partner in self:
            # Todas las oportunidades y leads del partner
            all_leads = partner.x_opportunity_ids | partner.x_lead_ids

            # Mensajes relacionados con actividades hechas
            last_done_msg = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', 'in', all_leads.ids),
                ('message_type', '=', 'notification'),
                ('subtype_id.name', '=', 'Actividades'),
                ('body', 'ilike', 'hecho'),
            ], order='date desc', limit=1)

            partner.last_activity_done_date = last_done_msg.date.date() if last_done_msg else False

    def _compute_pending_activity_counts(self):
        for partner in self:
            # Buscar los leads y oportunidades relacionados
            leads = self.env['crm.lead'].search([
                ('partner_id', '=', partner.id),
                ('type', '=', 'lead')
            ])
            opportunities = self.env['crm.lead'].search([
                ('partner_id', '=', partner.id),
                ('type', '=', 'opportunity')
            ])
    
            # IDs
            lead_ids = leads.ids
            opp_ids = opportunities.ids
    
            # Contadores
            lead_activity_count = self.env['mail.activity'].search_count([
                ('res_model', '=', 'crm.lead'),
                ('res_id', 'in', lead_ids),
                ('date_done', '=', False),
            ]) if lead_ids else 0
    
            opp_activity_count = self.env['mail.activity'].search_count([
                ('res_model', '=', 'crm.lead'),
                ('res_id', 'in', opp_ids),
                ('date_done', '=', False),
            ]) if opp_ids else 0
    
            # Asignar a los campos
            partner.x_pending_lead_activity_count = lead_activity_count
            partner.x_pending_opportunity_activity_count = opp_activity_count
            partner.x_pending_activity_count = lead_activity_count + opp_activity_count

    def action_view_pending_activities(self):
        self.ensure_one()

        leads = self.env['crm.lead'].search([('partner_id', '=', self.id)])
        lead_ids = leads.ids

        return {
            'name': 'Actividades pendientes de Leads',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.activity',
            'view_mode': 'list,form',
            'domain': [
                ('res_model', '=', 'crm.lead'),
                ('res_id', 'in', lead_ids),
                ('date_done', '=', False)
            ],
            'context': {
                'default_res_model': 'crm.lead',
            },
            'target': 'current',
        }