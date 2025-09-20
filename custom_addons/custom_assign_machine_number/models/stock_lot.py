from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.lot'

    x_machine_number = fields.Char(string="Número de máquina", copy=False, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        lots = super().create(vals_list)

        # Verificar si estamos en modo de instalación o carga de datos
        if self.env.context.get('install_mode') or self.env.context.get('module') or self.env.context.get('import_file'):
            # Durante la instalación o importación, no intentamos heredar el número de máquina
            return lots

        for lot in lots:
            if not lot.x_machine_number:
                try:
                    lot._try_inherit_machine_number_from_mo()
                except Exception:
                    # Capturamos cualquier excepción para evitar que falle la creación del lote
                    pass

        return lots

    def _try_inherit_machine_number_from_mo(self):
        """
        Si el lote se está creando como resultado de una fabricación,
        intenta heredar el número de máquina desde los lotes consumidos.
        """
        self.ensure_one()
        
        # Verificar si estamos en modo de instalación de datos demo
        if self.env.context.get('install_mode'):
            # Saltamos este proceso durante la instalación de datos demo
            return
            
        # Buscar producción relacionada con este lote
        # Solo usar lot_producing_ids que es el campo en Odoo 19
        production = False
        try:
            production = self.env['mrp.production'].search([
                ('lot_producing_ids', 'in', self.id),
            ], limit=1)
        except Exception:
            # Si hay cualquier error en la búsqueda, simplemente continuamos
            pass

        if not production:
            return

        # Buscar lotes consumidos
        raw_lots = production.move_raw_ids.mapped('move_line_ids.lot_id')
        machine_lot = raw_lots.filtered(lambda l: l.x_machine_number)

        if machine_lot:
            self.x_machine_number = machine_lot[0].x_machine_number
