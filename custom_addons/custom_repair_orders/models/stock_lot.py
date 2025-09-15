from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.lot'

    x_machine_number = fields.Char(string="Número de máquina", index=True)
    display_name = fields.Char(compute='_compute_display_name', store=False)

    @api.depends_context('lot_display')
    @api.depends('name', 'x_machine_number')
    def _compute_display_name(self):
        use_machine = self.env.context.get('lot_display') == 'machine'
        for lot in self:
            lot.display_name = lot.x_machine_number if use_machine and lot.x_machine_number else lot.name

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=80, name_get_uid=None):
        args = list(args or [])
        if name:
            # Busca por nº de serie o nº de máquina
            args = ['|', ('name', operator, name), ('x_machine_number', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
