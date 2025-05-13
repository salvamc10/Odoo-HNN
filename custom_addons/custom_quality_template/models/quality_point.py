from odoo import models, fields, api  # type: ignore

class QualityPoint(models.Model):
    _inherit = 'quality.point'

    template_id = fields.Many2one('workcenter.operation.template', string="Plantilla origen")
    linked_operation_id = fields.Many2one('mrp.routing.workcenter', string="Operación clonada")

    origin_point_id = fields.Many2one(
        'quality.point',
        string="Punto de origen",
        help="Referencia al punto de control original que generó este punto clonado."
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.template_id and not rec.linked_operation_id:
                rec._create_linked_points()
        return records

    def write(self, vals):
        template_set = 'template_id' in vals
        category_changed = 'product_category_ids' in vals
        product_changed = 'product_ids' in vals

        res = super().write(vals)

        for rec in self:
            # Si es punto base (no clon) y tiene plantilla asignada
            if rec.template_id and not rec.linked_operation_id:
                # Siempre actualizar datos de clones
                rec._update_linked_points()
                rec._prune_linked_points()
                rec._sync_linked_points()

                # Si cambia template o productos/categorías, intenta generar nuevos clones
                if template_set or category_changed or product_changed:
                    rec._create_linked_points()

        return res

    def unlink(self):
        for rec in self:
            # Si es un punto base con plantilla y no es clon
            if rec.template_id and not rec.linked_operation_id:
                # Solo borra los que apuntan a este punto como origen
                linked = self.env['quality.point'].search([
                    ('origin_point_id', '=', rec.id),
                    ('linked_operation_id', '!=', False)
                ])
                linked.unlink()
        return super().unlink()

    def _create_linked_points(self):
        QualityPoint = self.env['quality.point']
        Product = self.env['product.product']
        MrpBom = self.env['mrp.bom']

        for rec in self:
            operations = rec.template_id.operation_ids if rec.template_id else []

            for operation in operations:
                # Buscar todas las BOM con esta operación asignada
                boms = MrpBom.search([('operation_ids', 'in', operation.id)])

                # Filtrar productos específicos (si están definidos)
                if rec.product_ids:
                    boms = boms.filtered(lambda b: b.product_tmpl_id.product_variant_ids & rec.product_ids)

                # Filtrar categorías (si están definidas y no hay productos específicos)
                elif rec.product_category_ids:
                    boms = boms.filtered(lambda b: b.product_tmpl_id.categ_id.id in rec.product_category_ids.ids)

                # Productos resultantes según filtros
                products = boms.mapped('product_tmpl_id.product_variant_ids')

                for product in products:
                    # Comprobar duplicados
                    exists = QualityPoint.search([
                        ('linked_operation_id', '=', operation.id),
                        ('product_ids', 'in', product.id),
                        '|',
                        ('origin_point_id', '=', rec.id),
                        ('name', '=', rec.name),
                    ], limit=1)

                    if exists:
                        continue

                    QualityPoint.create({
                        'title': rec.title,
                        'name': rec.name,
                        'template_id': rec.template_id.id,
                        'linked_operation_id': operation.id,
                        'origin_point_id': rec.id,
                        'operation_id': operation.id,
                        'product_ids': [(6, 0, [product.id])],
                        'product_category_ids': [(6, 0, rec.product_category_ids.ids)],
                        'team_id': rec.team_id.id,
                        'company_id': rec.company_id.id,
                        'user_id': rec.user_id.id,
                        'note': rec.note,
                        'test_type_id': rec.test_type_id.id,
                        'test_type': rec.test_type,
                        'test_report_type': rec.test_report_type,
                        'picking_type_ids': [(6, 0, rec.picking_type_ids.ids)],
                        'is_workorder_step': True,
                    })

    def _update_linked_points(self):
        for rec in self:
            # Solo actualiza clones con mismo nombre, plantilla y operación relacionada
            clones = self.env['quality.point'].search([
                ('template_id', '=', rec.template_id.id),
                ('linked_operation_id', '!=', False),
                ('name', '=', rec.name),
            ])
            for clone in clones:
                clone.write({
                    'title': rec.title,
                    'name': rec.name,
                    'product_ids': [(6, 0, rec.product_ids.ids)],
                    'product_category_ids': [(6, 0, rec.product_category_ids.ids)],
                    'team_id': rec.team_id.id,
                    'company_id': rec.company_id.id,
                    'user_id': rec.user_id.id,
                    'note': rec.note,
                    'test_type_id': rec.test_type_id.id,
                    'test_type': rec.test_type,
                    'test_report_type': rec.test_report_type,
                    'picking_type_ids': [(6, 0, rec.picking_type_ids.ids)],
                    'is_workorder_step': True,
                })

    def _prune_linked_points(self):
        Product = self.env['product.product']
        MrpBom = self.env['mrp.bom']

        for rec in self:
            if not rec.template_id:
                continue

            operations = rec.template_id.operation_ids
            valid_product_ids = set()

            for operation in operations:
                boms = MrpBom.search([('operation_ids', 'in', operation.id)])

                if rec.product_ids:
                    boms = boms.filtered(lambda b: b.product_tmpl_id.product_variant_ids & rec.product_ids)
                elif rec.product_category_ids:
                    boms = boms.filtered(lambda b: b.product_tmpl_id.categ_id.id in rec.product_category_ids.ids)

                products = boms.mapped('product_tmpl_id.product_variant_ids')
                valid_product_ids.update(products.ids)

            # Buscar clones del punto original
            clones = self.env['quality.point'].search([
                ('origin_point_id', '=', rec.id),
                ('linked_operation_id', '!=', False)
            ])

            for clone in clones:
                clone_product_ids = set(clone.product_ids.ids)
                if not (clone_product_ids & valid_product_ids):
                    # Solo borrar si ya no es válido
                    clone.unlink()

    def _sync_linked_points(self):
        QualityPoint = self.env['quality.point']
        Product = self.env['product.product']
        MrpBom = self.env['mrp.bom']

        for rec in self:
            if not rec.template_id or rec.linked_operation_id:
                continue

            # 1. Borrar clones actuales (si existen)
            existing_clones = QualityPoint.search([
                ('origin_point_id', '=', rec.id),
                ('linked_operation_id', '!=', False)
            ])
            existing_clones.unlink()

            # 2. Buscar productos que aplican
            products_to_create = set()
            operations = rec.template_id.operation_ids

            for operation in operations:
                boms = MrpBom.search([('operation_ids', 'in', operation.id)])

                if rec.product_ids:
                    boms = boms.filtered(lambda b: b.product_tmpl_id.product_variant_ids & rec.product_ids)
                elif rec.product_category_ids:
                    boms = boms.filtered(lambda b: b.product_tmpl_id.categ_id.id in rec.product_category_ids.ids)

                products = boms.mapped('product_tmpl_id.product_variant_ids')
                for product in products:
                    products_to_create.add((product.id, operation.id))

            # 3. Crear los puntos que deben existir
            for product_id, operation_id in products_to_create:
                QualityPoint.create({
                    'title': rec.title,
                    'name': rec.name,
                    'template_id': rec.template_id.id,
                    'linked_operation_id': operation_id,
                    'origin_point_id': rec.id,
                    'operation_id': operation_id,
                    'product_ids': [(6, 0, [product_id])],
                    'product_category_ids': [(6, 0, rec.product_category_ids.ids)],
                    'team_id': rec.team_id.id,
                    'company_id': rec.company_id.id,
                    'user_id': rec.user_id.id,
                    'note': rec.note,
                    'test_type_id': rec.test_type_id.id,
                    'test_type': rec.test_type,
                    'test_report_type': rec.test_report_type,
                    'picking_type_ids': [(6, 0, rec.picking_type_ids.ids)],
                    'is_workorder_step': True,
                })

    def name_get(self):
        return [(rec.id, rec.title or rec.name) for rec in self]
    