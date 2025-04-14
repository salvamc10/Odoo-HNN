from odoo import models, fields, api # type: ignore

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Campo para relacionar el contacto de mailing creado
    mailing_contact_id = fields.Many2one('mailing.contact', string="Contacto en Mailing")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Al crear un partner, si se incluye un email, se busca la lista de mailing 
        "BBDD BHIOR BASE DE DATOS ESPAÑA" y se crea un registro en mailing.contact, 
        asignándolo al partner.
        """
        partners = super(ResPartner, self).create(vals_list)
        mailing_list = self.env['mailing.list'].search([('name', '=', 'BBDD BHIOR BASE DE DATOS ESPAÑA')], limit=1)
        if mailing_list:
            for partner in partners:
                if partner.email:
                    # Sólo se crea si aún no existe un contacto en mailing
                    if not partner.mailing_contact_id:
                        mailing_contact = self.env['mailing.contact'].create({
                            'email': partner.email,
                            'name': partner.name or '',
                            'list_ids': [(4, mailing_list.id)]
                        })
                        partner.mailing_contact_id = mailing_contact.id
        return partners

    def write(self, vals):
        """
        Al editar un partner, se comprueba si el campo 'email' está en los valores (vals).
        Si se edita el email:
            - Si ya existe un mailing.contact relacionado, se actualiza el email.
            - Si no existe y se añade el email, se crea el registro en la lista de mailing.
        """
        res = super(ResPartner, self).write(vals)
        mailing_list = self.env['mailing.list'].search([('name', '=', 'BBDD BHIOR BASE DE DATOS ESPAÑA')], limit=1)
        for partner in self:
            if 'email' in vals:
                if partner.mailing_contact_id:
                    # Actualizamos el email en el mailing.contact relacionado
                    partner.mailing_contact_id.write({'email': partner.email})
                else:
                    # Si el partner no tenía mailing.contact y ahora tiene email, se crea el registro
                    if partner.email and mailing_list:
                        mailing_contact = self.env['mailing.contact'].create({
                            'email': partner.email,
                            'name': partner.name or '',
                            'list_ids': [(4, mailing_list.id)]
                        })
                        partner.mailing_contact_id = mailing_contact.id
        return res
