# -*- coding: utf-8 -*-
from odoo import fields, models

class RepairWorksheetTemplateLoad(models.TransientModel):
    _name = 'repair.worksheet.template.load.wizard'
    _description = 'Asistente para cargar plantilla de hoja de trabajo'

    repair_id = fields.Many2one('repair.order', "Reparación", required=True)

    def action_generate_new_template(self):
        new_template = self.env['worksheet.template'].sudo().create({
            'name': 'Instalación y Mantenimiento de Equipos',
            'res_model': 'repair.order',
        })
        default_form_view = self.env['ir.ui.view'].sudo().search([
            ('model', '=', new_template.model_id.model), 
            ('type', '=', 'form')
        ], limit=1)
        
        extend_view_id = self.env["ir.ui.view"].sudo().create({
            "type": "form",
            "name": 'template_view_' + new_template.name.replace(' ', '_'),
            "model": new_template.model_id.model,
            "inherit_id": default_form_view.id,
            "arch": """
                    <xpath expr="//form/sheet" position="replace">
                        <sheet>
                            <group invisible="context.get('studio') or context.get('default_x_repair_order_id')">
                                <div class="oe_title">
                                    <h1>
                                        <field name="x_repair_order_id" readonly="1"/>
                                    </h1>
                                </div>
                            </group>
                            <group class="o_repair_worksheet_form">
                                <field name="x_name"/>
                                <field name="x_manufacturer" options="{'no_create':true, 'no_open':true}"/>
                                <field name="x_serial_number"/>
                                <field name="x_intervention_type" widget="radio"/>
                                <field name="x_description"/>
                                <field name="x_date"/>
                                <field name="x_worker_signature" widget="signature"/>
                            </group>
                        </sheet>
                    </xpath>
                    """,
        })
        new_template._generate_qweb_report_template(form_view_id=extend_view_id.id)
        self.repair_id.worksheet_template_id = new_template
        return self.repair_id.open_repair_worksheet()

    def action_open_template(self):
        return self.repair_id.open_repair_worksheet()
