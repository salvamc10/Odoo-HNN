# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe create para crear firmas para todos los usuarios."""
        companies = super().create(vals_list)
        for company in companies:
            # Obtener todos los usuarios que tienen acceso a esta compañía
            users = self.env['res.users'].search([
                ('company_ids', 'in', company.id)
            ])
            # Crear firmas para cada usuario
            for user in users:
                self.env['user.company.signature'].create({
                    'user_id': user.id,
                    'company_id': company.id,
                    'signature': user.signature or '',
                })
        return companies