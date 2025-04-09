# -*- coding: utf-8 -*-
from odoo import models, fields

"""
Este módulo extiende el modelo de Quality Point para permitir la asignación de puntos de control a centros de trabajo específicos.
Esto es útil para gestionar la calidad de los productos en diferentes etapas del proceso de producción.
"""

class QualityPoint(models.Model):
    _inherit = 'quality.point'

    # Nuevo campo: permite asignar un punto de control a un centro de trabajo específico.
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Centro de trabajo',
        help='Si se define, este punto de control se aplicará a las órdenes que pasen por este centro.'
    )
