from odoo import models

class WorksheetTemplate(models.Model):
    _inherit = "worksheet.template"

    def _get_repair_order_manager_group(self):
        return self.env.ref("custom_repair_product.group_repair_manager")
    
    def _get_repair_order_user_group(self):
        return self.env.ref("custom_repair_product.group_repair_user")
    
    def _get_repair_order_access_all_groups(self):
        return self._get_repair_order_manager_group() | self._get_repair_order_user_group()
    
    def _get_repair_order_module_name(self):
        return "custom_repair_product"
