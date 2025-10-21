from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    mailing_contact_id = fields.Many2one('mailing.contact', string="Contacto en Mailing")

    def _get_mailing_list_ids(self):
        self.ensure_one()
        
        company_id = self.company_id.id if self.company_id else False
        state_id = self.state_id.id if self.state_id else False
        
        if company_id == 1:
            return [2]
        elif company_id == 2:
            if state_id in [420, 451]:
                return [12]
            elif state_id == 421:
                return [25]
            elif state_id == 419:
                return [27]
            else:
                return []
        elif company_id == 6:
            return [78]
        else:
            return []

    @api.model_create_multi
    def create(self, vals_list):
        partners = super(ResPartner, self).create(vals_list)
        
        for partner in partners:
            if partner.email:
                mailing_list_ids = partner._get_mailing_list_ids()
                
                if not mailing_list_ids:
                    continue
                
                existing_contact = self.env['mailing.contact'].search([
                    ('email', '=', partner.email)
                ], limit=1)
                
                if existing_contact:
                    partner.mailing_contact_id = existing_contact.id
                    for list_id in mailing_list_ids:
                        if list_id not in existing_contact.list_ids.ids:
                            existing_contact.write({'list_ids': [(4, list_id)]})
                else:
                    new_contact = self.env['mailing.contact'].create({
                        'email': partner.email,
                        'list_ids': [(4, list_id) for list_id in mailing_list_ids]
                    })
                    partner.mailing_contact_id = new_contact.id
        
        return partners

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        
        relevant_fields = ['email', 'company_id', 'state_id']
        
        if any(field in vals for field in relevant_fields):
            for partner in self:
                if partner.email:
                    mailing_list_ids = partner._get_mailing_list_ids()
                    new_email = vals.get('email', partner.email)
                    current_mailing = partner.mailing_contact_id
                    
                    existing_contact = self.env['mailing.contact'].search([
                        ('email', '=', new_email)
                    ], limit=1)
                    
                    if existing_contact:
                        if current_mailing and current_mailing.id != existing_contact.id:
                            others = self.search([
                                ('mailing_contact_id', '=', current_mailing.id),
                                ('id', '!=', partner.id)
                            ])
                            if not others:
                                current_mailing.unlink()
                            partner.mailing_contact_id = existing_contact.id
                        else:
                            if not current_mailing:
                                partner.mailing_contact_id = existing_contact.id
                        
                        if mailing_list_ids:
                            for list_id in mailing_list_ids:
                                if list_id not in existing_contact.list_ids.ids:
                                    existing_contact.write({'list_ids': [(4, list_id)]})
                    
                    else:
                        if current_mailing:
                            current_mailing.write({'email': new_email})
                            if mailing_list_ids:
                                current_mailing.write({'list_ids': [(6, 0, mailing_list_ids)]})
                            else:
                                current_mailing.write({'list_ids': [(5, 0, 0)]})
                        else:
                            if mailing_list_ids:
                                new_contact = self.env['mailing.contact'].create({
                                    'email': new_email,
                                    'list_ids': [(4, list_id) for list_id in mailing_list_ids]
                                })
                                partner.mailing_contact_id = new_contact.id
        
        return res

    def unlink(self):
        mailing_contacts = self.mapped('mailing_contact_id')
        res = super(ResPartner, self).unlink()
        for mailing in mailing_contacts:
            ref_count = self.env['res.partner'].search_count([
                ('mailing_contact_id', '=', mailing.id)
            ])
            if ref_count == 0:
                mailing.unlink()
        return res
