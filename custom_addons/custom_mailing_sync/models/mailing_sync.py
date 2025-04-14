from odoo import models, fields, api # type: ignore

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
            ('name', '=', 'BBDD BHIOR BASE DE DATOS ESPAÑA')
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
            ('name', '=', 'BBDD BHIOR BASE DE DATOS ESPAÑA')
        ], limit=1)
        for partner in self:
            if 'email' in vals and partner.email and mailing_list:
                new_email = vals.get('email')
                existing_contact = self.env['mailing.contact'].search([
                    ('email', '=', new_email)
                ], limit=1)
                if existing_contact:
                    # Si el mailing_contact es distinto al actual, lo reasociamos
                    if partner.mailing_contact_id != existing_contact:
                        partner.mailing_contact_id = existing_contact.id
                        if mailing_list.id not in existing_contact.list_ids.ids:
                            existing_contact.write({'list_ids': [(4, mailing_list.id)]})
                else:
                    # Si no existe, pero el partner ya tenía un mailing_contact,
                    # actualizamos su email para sincronizarlo
                    if partner.mailing_contact_id:
                        partner.mailing_contact_id.write({'email': new_email})
                    else:
                        new_contact = self.env['mailing.contact'].create({
                            'email': new_email,
                            'name': partner.name or '',
                            'list_ids': [(4, mailing_list.id)]
                        })
                        partner.mailing_contact_id = new_contact.id
        return res

    def unlink(self):
        for partner in self:
            if partner.mailing_contact_id:
                # Verifica si hay otros partners asociados al mismo mailing_contact
                others = self.search([
                    ('mailing_contact_id', '=', partner.mailing_contact_id.id),
                    ('id', '!=', partner.id)
                ])
                # Si no hay otros, elimina el mailing_contact
                if not others:
                    partner.mailing_contact_id.unlink()
        return super(ResPartner, self).unlink()
