from odoo import models

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def _create_quality_checks(self):
        res = super()._create_quality_checks()
        for workorder in self:
            plantilla = self.env['quality.point.template'].search([
                ('workcenter_id', '=', workorder.workcenter_id.id),
                ('categ_id', '=', workorder.product_id.categ_id.id)
            ])

            for template in plantilla:
                for point in template.quality_point_ids:
                    self.env['quality.check'].create({
                        'workorder_id': workorder.id,
                        'point_id': point.id,
                        'product_id': workorder.product_id.id,
                    })
        return res
    