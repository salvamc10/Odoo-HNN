from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Campo para relacionar el contacto de mailing creado
    mailing_contact_id = fields.Many2one('mailing.contact', string="Contacto en Mailing")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Al crear un partner, si se incluye un email, se busca primero 
        si ya existe en mailing.contact. De existir, lo reutiliza; 
        si no, se crea uno nuevo. Finalmente se asocia (mailing_contact_id) 
        al partner.
        """
        partners = super(ResPartner, self).create(vals_list)
        mailing_list = self.env['mailing.list'].search([
            ('name', '=', '10. BHIOR BASE DE DATOS ESPAÑA B2B')
        ], limit=1)
        
        for partner in partners:
            if partner.email and mailing_list:
                # Buscar si ya existe un mailing.contact con el mismo email
                existing_contact = self.env['mailing.contact'].search([
                    ('email', '=', partner.email)
                ], limit=1)
                
                if existing_contact:
                    # Si ya existe, asociarlo al partner.
                    # Y asegurarnos de que esté en la lista de correo
                    partner.mailing_contact_id = existing_contact.id
                    if mailing_list.id not in existing_contact.list_ids.ids:
                        existing_contact.write({'list_ids': [(4, mailing_list.id)]})
                else:
                    # Si no existe, creamos un nuevo mailing.contact
                    new_contact = self.env['mailing.contact'].create({
                        'email': partner.email,
                        'name': partner.name or '',
                        'list_ids': [(4, mailing_list.id)]
                    })
                    partner.mailing_contact_id = new_contact.id
        return partners

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        mailing_list = self.env['mailing.list'].search([
            ('name', '=', '10. BHIOR BASE DE DATOS ESPAÑA B2B')
        ], limit=1)
        for partner in self:
            if 'email' in vals and partner.email and mailing_list:
                new_email = vals.get('email')
                current_mailing = partner.mailing_contact_id
                # Buscar un mailing.contact con el nuevo email
                existing_contact = self.env['mailing.contact'].search([
                    ('email', '=', new_email)
                ], limit=1)
                if existing_contact:
                    # Si hay un mailing_contact existente y es distinto al actual:
                    if current_mailing and current_mailing.id != existing_contact.id:
                        # Comprueba si el mailing_contact actual no está usado por otros partners
                        others = self.search([
                            ('mailing_contact_id', '=', current_mailing.id),
                            ('id', '!=', partner.id)
                        ])
                        if not others:
                            # Si no se usa en ningún otro partner, eliminarlo
                            current_mailing.unlink()
                        # Asocia el partner al mailing_contact existente
                        partner.mailing_contact_id = existing_contact.id
                        # Asegura que el mailing_contact esté vinculado a la lista
                        if mailing_list.id not in existing_contact.list_ids.ids:
                            existing_contact.write({'list_ids': [(4, mailing_list.id)]})
                    else:
                        # Si no tenía mailing_contact, lo asocia al existente
                        if not current_mailing:
                            partner.mailing_contact_id = existing_contact.id
                            if mailing_list.id not in existing_contact.list_ids.ids:
                                existing_contact.write({'list_ids': [(4, mailing_list.id)]})
                else:
                    # No se encontró mailing_contact con el nuevo email:
                    if current_mailing:
                        # Actualiza el mailing_contact actual con el nuevo email
                        current_mailing.write({'email': new_email})
                    else:
                        # Crea un nuevo mailing_contact y lo asocia al partner
                        new_contact = self.env['mailing.contact'].create({
                            'email': new_email,
                            'name': partner.name or '',
                            'list_ids': [(4, mailing_list.id)]
                        })
                        partner.mailing_contact_id = new_contact.id
        return res

    def unlink(self):
        # Recopila los mailing_contact asociados a estos partners antes de eliminarlos
        mailing_contacts = self.mapped('mailing_contact_id')
        res = super(ResPartner, self).unlink()
        # Para cada mailing_contact, si ya no está referenciado por ningún partner, se elimina
        for mailing in mailing_contacts:
            ref_count = self.env['res.partner'].search_count([
                ('mailing_contact_id', '=', mailing.id)
            ])
            if ref_count == 0:
                mailing.unlink()
        return res
