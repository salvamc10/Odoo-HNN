# -*- coding: utf-8 -*-
from odoo import fields, models

class RepairWorksheetTemplateLoad(models.TransientModel):
    _name = 'repair.worksheet.template.load.wizard'
    _description = 'Load the worksheet template for repair orders'

    repair_order_id = fields.Many2one('repair.order', "Repair Order", required=True, default=lambda self: self._context.get('active_id'))

    def action_generate_new_template(self):
        new_template = self.env['worksheet.template'].sudo().create({
            'name': 'Repair Order Worksheet Template',
            'res_model': 'repair.order',
        })
        new_template._create_demo_data_fsm(model_id=new_template.model_id.id)  # Método de worksheet para datos demo
        default_form_view = self.env['ir.ui.view'].sudo().search([('model', '=', new_template.model_id.model), ('type', '=', 'form')], limit=1)
        if default_form_view:
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
                                <field name="name" invisible="1"/>
                                <field name="type"/>  <!-- Campo personalizado de tu modelo -->
                                <field name="consulta_ids" widget="one2many" readonly="1"/>
                                <field name="x_repair_worksheet_template_id" invisible="1"/>
                                <field name="description" string="Descripción de Reparación"/>
                                <field name="state" widget="statusbar"/>
                            </group>
                        </sheet>
                    </xpath>
                    """,
            }).id
            new_template._generate_qweb_report_template(form_view_id=extend_view_id)
        self.repair_order_id.x_repair_worksheet_template_id = new_template
        return self.repair_order_id.action_view_worksheet()

    def action_open_template(self):
        return self.repair_order_id.action_view_worksheet()