# -*- coding: utf-8 -*-
from . import models

def pre_init_hook(cr):
    """ Este hook se ejecuta antes de la instalación del módulo """
    from odoo import api, SUPERUSER_ID # type: ignore
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['stock.lot']._create_missing_field()
