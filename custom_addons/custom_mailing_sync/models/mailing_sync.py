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
        """
        Al editar un partner, si se modifica el 'email', 
        se busca si ya existe en mailing.contact. 
        Si existe, se asocia. Si no, se crea uno nuevo.
        """
        res = super(ResPartner, self).write(vals)
        
        mailing_list = self.env['mailing.list'].search([
            ('name', '=', 'BBDD BHIOR BASE DE DATOS ESPAÑA')
        ], limit=1)
        
        for partner in self:
            # Solo si el email se ha modificado
            if 'email' in vals and partner.email and mailing_list:
                existing_contact = self.env['mailing.contact'].search([
                    ('email', '=', partner.email)
                ], limit=1)
                
                if existing_contact:
                    # Asociar el partner a este contacto existente
                    partner.mailing_contact_id = existing_contact.id
                    # Asegurar que esté en la lista
                    if mailing_list.id not in existing_contact.list_ids.ids:
                        existing_contact.write({'list_ids': [(4, mailing_list.id)]})
                else:
                    # Crear nuevo contacto si no existe ninguno
                    new_contact = self.env['mailing.contact'].create({
                        'email': partner.email,
                        'name': partner.name or '',
                        'list_ids': [(4, mailing_list.id)]
                    })
                    partner.mailing_contact_id = new_contact.id
        return res
