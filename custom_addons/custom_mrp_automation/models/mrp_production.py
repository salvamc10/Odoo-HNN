from odoo import models, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        context = dict(self._context or {})
        skip_auto_confirm = context.pop('skip_auto_confirm', False)
        no_create_moves = context.pop('no_create_moves', False)

        records = super(MrpProduction, self.with_context(context)).create(vals_list)

        for mo in records:
            if skip_auto_confirm and mo.state != 'draft':
                mo.write({'state': 'draft'})
            if no_create_moves and mo.move_raw_ids:
                mo.move_raw_ids.unlink()

        return records