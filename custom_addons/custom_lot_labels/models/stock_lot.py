# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID # type: ignore

class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Declaración del campo (para que sea visible en Odoo)
    x_machine_number = fields.Char(string="Machine Number")

    @api.model
    def _create_missing_field(self):
        """ Verifica si el campo existe, si no, lo crea dinámicamente """
        field_name = 'x_machine_number'
        model_name = 'stock.lot'

        # Verifica si el campo ya existe
        field = self.env['ir.model.fields'].sudo().search([
            ('name', '=', field_name),
            ('model', '=', model_name)
        ], limit=1)

        if not field:
            # Crea el campo dinámicamente
            self.env['ir.model.fields'].sudo().create({
                'name': field_name,
                'model': model_name,
                'field_description': 'Machine Number',
                'ttype': 'char',
                'state': 'manual',
            })
            print(f"✅ Campo '{field_name}' creado exitosamente en '{model_name}'.")
        else:
            print(f"⚠️ El campo '{field_name}' ya existe en '{model_name}'.")
