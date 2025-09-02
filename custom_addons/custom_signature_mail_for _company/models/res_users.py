# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    company_signature_ids = fields.One2many(
        'user.company.signature',
        'user_id',
        string='Firmas por compañía'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe create para crear firmas para todas las compañías."""
        users = super().create(vals_list)
        for user in users:
            # Crear firmas para todas las compañías permitidas
            for company in user.company_ids:
                self.env['user.company.signature'].create({
                    'user_id': user.id,
                    'company_id': company.id,
                    'signature': user.signature or '',
                })
        return users

    def write(self, vals):
        """Sobrescribe write para mantener sincronizadas las firmas."""
        res = super().write(vals)
        if 'company_ids' in vals:
            for user in self:
                # Crear firmas para las nuevas compañías
                existing_sigs = user.company_signature_ids.mapped('company_id')
                for company in user.company_ids - existing_sigs:
                    self.env['user.company.signature'].create({
                        'user_id': user.id,
                        'company_id': company.id,
                        'signature': user.signature or '',
                    })
        return res

    @api.depends('company_id')
    def _compute_signature(self):
        """Sobrescribe el cálculo de firma para usar la firma específica de la compañía."""
        for user in self:
            company_signature = self.env['user.company.signature'].search([
                ('user_id', '=', user.id),
                ('company_id', '=', user.company_id.id)
            ], limit=1)
            user.signature = company_signature.signature if company_signature else ''