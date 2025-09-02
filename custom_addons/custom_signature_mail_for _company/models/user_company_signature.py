# -*- coding: utf-8 -*-

from odoo import models, fields, api

class UserCompanySignature(models.Model):
    _name = 'user.company.signature'
    _description = 'Firmas de usuario por compañía'

    user_id = fields.Many2one('res.users', string='Usuario', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, ondelete='cascade')
    signature = fields.Html(string='Firma', sanitize=False)
    
    _sql_constraints = [
        ('unique_user_company', 'unique(user_id, company_id)',
         'Ya existe una firma para este usuario en esta compañía.')
    ]
