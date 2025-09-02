# -*- coding: utf-8 -*-

from odoo import models, api

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def generate_email(self, res_ids, fields):
        """Sobrescribe generate_email para usar la firma específica de la compañía."""
        results = super().generate_email(res_ids, fields)

        # Si es un solo ID, convertirlo a lista
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            is_single = True
        else:
            is_single = False

        for res_id in res_ids:
            email_values = results[res_id]
            
            # Obtener el usuario actual y su firma para la compañía actual
            user = self.env.user
            company_signature = self.env['user.company.signature'].search([
                ('user_id', '=', user.id),
                ('company_id', '=', user.company_id.id)
            ], limit=1)

            if company_signature and company_signature.signature:
                # Actualizar la firma en el cuerpo del correo
                if email_values.get('body_html'):
                    signature = company_signature.signature
                    body = email_values['body_html']
                    # Reemplazar la firma actual con la firma específica de la compañía
                    if user.signature:
                        body = body.replace(user.signature, signature)
                    else:
                        body = body + signature
                    email_values['body_html'] = body

        return results if not is_single else results[res_ids[0]]