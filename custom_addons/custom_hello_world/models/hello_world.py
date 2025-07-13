
from odoo import models, fields # type: ignore

class HelloWorld(models.Model):
    _name = "custom.hello.world"
    _description = "Hello World"

    name = fields.Char(string="Name", required=True)
