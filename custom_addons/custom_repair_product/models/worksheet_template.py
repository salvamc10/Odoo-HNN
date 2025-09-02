# en models/worksheet_template.py
from odoo import api, models, _
import base64, logging
_logger = logging.getLogger(__name__)

class WorksheetTemplate(models.Model):
    _inherit = "worksheet.template"

    @api.model
    def _get_documents_folder(self):
        """Devuelve/crea carpeta si el módulo documents existe; si no, None."""
        # Si el modelo no existe (no hay documents), no intentes crear nada
        if 'documents.folder' not in self.env:
            return False
        env = self.env['documents.folder'].sudo()
        folder = False
        try:
            folder = self.env.ref('custom_repair_product.folder_worksheets')
        except Exception:
            folder = env.search([('name', '=', 'Hojas de Trabajo')], limit=1)
            if not folder:
                folder = env.create({'name': 'Hojas de Trabajo', 'sequence': 10})
        return folder

    @api.model
    def _save_one_record_to_documents(self, rec):
        Report = self.env['ir.actions.report'].sudo().search([
            ('model', '=', rec._name),
            ('report_name', '=', 'custom_repair_product.report_worksheet_generic')
        ], limit=1)
        if not Report:
            _logger.warning("No report action for model %s", rec._name)
            return
        pdf, _ = Report._render_qweb_pdf([rec.id])

        repair = self._find_related_repair_order(rec)
        base_name = f"Hoja de Trabajo - {repair.name if repair else rec.display_name}"

        attach = self.env['ir.attachment'].sudo().create({
            'name': f'{base_name}.pdf',
            'datas': base64.b64encode(pdf),
            'mimetype': 'application/pdf',
            'res_model': 'repair.order' if repair else rec._name,
            'res_id': repair.id if repair else rec.id,
        })

        # Solo crea documents.document si el modelo existe
        if 'documents.document' in self.env:
            folder = self._get_documents_folder()
            self.env['documents.document'].sudo().create({
                'attachment_id': attach.id,
                'folder_id': folder.id if folder else False,
                'owner_id': self.env.user.id,
                'partner_id': repair.partner_id.id if repair else False,
            })


    def _get_repair_order_manager_group(self):
        return self.env.ref("custom_repair_product.group_repair_manager")
    
    def _get_repair_order_user_group(self):
        return self.env.ref("custom_repair_product.group_repair_user")
    
    def _get_repair_order_access_all_groups(self):
        return self._get_repair_order_manager_group() | self._get_repair_order_user_group()
    
    def _get_repair_order_module_name(self):
        return "custom_repair_product"