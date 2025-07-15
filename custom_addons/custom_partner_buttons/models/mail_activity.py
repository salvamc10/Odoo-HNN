from odoo import models, fields, api # type: ignore

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    lead_type = fields.Char(string="Tipo (Lead/Oportunidad)", compute='_compute_lead_type', store=False)

    @api.depends('res_model', 'res_id')
    def _compute_lead_type(self):
        for activity in self:
            activity.lead_type = ''
            if activity.res_model == 'crm.lead':
                lead = self.env['crm.lead'].browse(activity.res_id)
                if lead.exists():
                    tipo = lead.type or ''
                    activity.lead_type = 'Oportunidad' if tipo == 'opportunity' else 'Lead'
