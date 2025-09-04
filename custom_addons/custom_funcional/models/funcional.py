from odoo import fields, models

class CustomFuncional(models.Model):
    _name = 'custom.funcional'
    _description = 'Modelo para funcionalidades personalizadas'

    user_id = fields.Many2one('res.users', string='Usuario')
    res_model = fields.Char(string='Modelo relacionado', readonly=True)
    res_field = fields.Char(string='Campo relacionado', readonly=True)
    res_id = fields.Many2oneReference(string='ID relacionado', model_field="res_model", readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía', change_default=True, default=lambda self: self.env.company)
    