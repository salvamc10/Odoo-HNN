from odoo import api, models, _
import base64, logging
_logger = logging.getLogger(__name__)

class WorksheetTemplate(models.Model):
    _inherit = "worksheet.template"

    # --- Crear plantilla ---
    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if rec.model_id:
                rec._install_save_button_for_model(rec.model_id)
        return recs

    # --- Asignan/cambian el modelo dinámico ---
    def write(self, vals):
        res = super().write(vals)
        if 'model_id' in vals:
            for rec in self.filtered('model_id'):
                rec._install_save_button_for_model(rec.model_id)
        return res

    # ========== Instalación botón + acción por modelo dinámico ==========
    def _install_save_button_for_model(self, model):
        Server = self.env['ir.actions.server'].sudo()
        View = self.env['ir.ui.view'].sudo()

        # Asegura acción de reporte para este modelo x_...
        self._ensure_report_for_model(model)

        code = (
            "action = env['worksheet.template']._save_and_reset(records)\n"
        )
        act = Server.search([('model_id', '=', model.id), ('name', '=', 'Guardar en Documentos')], limit=1)
        if act:
            act.write({'code': code})
        else:
            act = Server.create({'name': 'Guardar en Documentos', 'model_id': model.id, 'state': 'code', 'code': code})
            
        # Inyecta botón en TODAS las vistas form del modelo x_...
        form_views = View.search([('model', '=', model.model), ('type', '=', 'form')])
        for base_form in form_views:
            name_key = f"[SaveBtn]{model.model}-{base_form.id}"
            if View.search([('inherit_id', '=', base_form.id), ('name', '=', name_key)], limit=1):
                continue
            has_sheet = '<sheet' in (base_form.arch_db or '')
            target = "//sheet" if has_sheet else "//form"
            arch = f"""
            <xpath expr="{target}" position="inside">
                <div class="oe_button_box" name="button_box">
                    <button type="action"
                            name="{act.id}"
                            class="oe_stat_button btn-primary oe_highlight">
                    <i class="fa fa-cloud-upload"/>
                    <span class="o_stat_text">Guardar en Documentos</span>
                    </button>
                </div>
            </xpath>
            """
            View.create({
                'name': name_key,
                'type': 'form',
                'model': model.model,
                'inherit_id': base_form.id,
                'arch_db': arch,
                'priority': 16,
            })

    # ========== Reporte genérico por modelo dinámico ==========
    def _ensure_report_for_model(self, model):
        Report = self.env['ir.actions.report'].sudo()
        action = Report.search([
            ('model', '=', model.model),
            ('report_name', '=', 'custom_repair_product.report_worksheet_generic')
        ], limit=1)
        if not action:
            action = Report.create({
                'name': _('Worksheet PDF'),
                'model': model.model,
                'report_type': 'qweb-pdf',
                'report_name': 'custom_repair_product.report_worksheet_generic',
                'print_report_name': "('Hoja de Trabajo - %s' % (object.display_name,))",
            })

            self.env['ir.model.data'].sudo().create({
                'module': 'custom_repair_product',
                'name': f"report_ws_{model.model.replace('.', '_')}",
                'model': 'ir.actions.report',
                'res_id': action.id,
                'noupdate': True,
            })
    

    # ========== Guardado en adjuntos / Documents ==========
    # en models/worksheet_template.py

    @api.model
    def _save_one_record_to_documents(self, rec):
        _logger.info("=== DEBUGGING PDF GENERATION ===")
        _logger.info("Record model: %s", rec._name)
        _logger.info("Record ID: %s", rec.id)
        _logger.info("Record exists: %s", rec.exists())
    
        # ✅ Verificar que el modelo existe
        if rec._name not in self.env:
            _logger.error("❌ Model %s not found in registry", rec._name)
            return
    
        # ✅ Verificar que el record existe
        if not rec.exists():
            _logger.error("❌ Record %s[%s] does not exist", rec._name, rec.id)
            return
    
        # 🔎 Buscar/asegurar la acción de reporte correcta para ESTE modelo
        Report = self.env['ir.actions.report'].sudo().search([
            ('model', '=', rec._name),
            ('report_name', '=', 'custom_repair_product.report_worksheet_generic')
        ], limit=1)
        if not Report:
            _logger.warning("❌ No report action for model %s. Creating…", rec._name)
            # crea acción de reporte para este modelo
            Report = self.env['ir.actions.report'].sudo().create({
                'name': _('Worksheet PDF'),
                'model': rec._name,
                'report_type': 'qweb-pdf',
                'report_name': 'custom_repair_product.report_worksheet_generic',
                'print_report_name': "('Hoja de Trabajo - %s' % (object.display_name,))",
            })
    
        # ⚖️ Alinear modelo si difiere
        if Report.model != rec._name:
            _logger.warning("⚠️ Report model (%s) != Record model (%s). Fixing…", Report.model, rec._name)
            Report.sudo().write({'model': rec._name})
    
        # 🆔 Asegurar xml_id único del action y usarlo para render (evita coger actions viejas)
        imd = self.env['ir.model.data'].sudo()
        report_xmlid = Report.get_external_id().get(Report.id)
        if not report_xmlid:
            name = f"report_ws_{rec._name.replace('.', '_')}"
            existing = imd.search([
                ('module', '=', 'custom_repair_product'),
                ('name', '=', name),
                ('model', '=', 'ir.actions.report'),
            ], limit=1)
            if existing:
                existing.write({'res_id': Report.id})
            else:
                imd.create({
                    'module': 'custom_repair_product',
                    'name': name,
                    'model': 'ir.actions.report',
                    'res_id': Report.id,
                    'noupdate': True,
                })
            report_xmlid = f"custom_repair_product.{name}"
    
        _logger.info("✅ Using report xml_id: %s (id=%s, model=%s)", report_xmlid, Report.id, Report.model)
    
        # 🖨️ Render PDF (firma compatible con industry_fsm)
        try:
            pdf, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_ref=report_xmlid, res_ids=[rec.id]
            )
            _logger.info("✅ PDF generated, size: %s bytes", len(pdf) if pdf else 0)
        except TypeError:
            # Fallback sin override
            pdf = self.env['ir.actions.report']._render_qweb_pdf(report_xmlid, [rec.id])[0]
        except Exception as e:
            _logger.error("❌ PDF generation failed: %s", e, exc_info=True)
            return
    
        # 💾 Guardar adjunto + Documents
        repair = self._find_related_repair_order(rec)
        base_name = f"Hoja de Trabajo - {repair.name if repair else rec.display_name}"
    
        try:
            attach = self.env['ir.attachment'].sudo().create({
                'name': f'{base_name}.pdf',
                'datas': base64.b64encode(pdf),
                'mimetype': 'application/pdf',
                'res_model': 'repair.order' if repair else rec._name,
                'res_id': repair.id if repair else rec.id,
            })
            _logger.info("✅ Attachment created: %s (ID: %s)", attach.name, attach.id)
    
            if 'documents.document' in self.env:
                folder = self._get_documents_folder()
                doc = self.env['documents.document'].sudo().create({
                    'attachment_id': attach.id,
                    'folder_id': folder.id if folder else False,
                    'owner_id': self.env.user.id,
                    'partner_id': repair.partner_id.id if repair else False,
                })
                _logger.info("✅ Document created: ID %s", doc.id)
        except Exception as e:
            _logger.error("❌ Failed to save attachment/document: %s", e, exc_info=True)
            return

    @api.model
    def _find_related_repair_order(self, rec):
        for fname, field in rec._fields.items():
            if getattr(field, 'type', '') == 'many2one' and getattr(field, 'comodel_name', '') == 'repair.order':
                return getattr(rec, fname)
        return False

    @api.model
    def _get_documents_folder(self):
        if 'documents.folder' not in self.env:
            return False
        try:
            return self.env.ref('custom_repair_product.folder_worksheets')
        except Exception:
            Folder = self.env['documents.folder'].sudo()
            folder = Folder.search([('name', '=', 'Hojas de Trabajo')], limit=1)
            return folder or Folder.create({'name': 'Hojas de Trabajo', 'sequence': 10})

    @api.model
    def _save_and_reset(self, records):
        for r in records:
            self._save_one_record_to_documents(r)
            self._reset_record_fields(r)  # limpia campos en el mismo record
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'OK', 'message': 'Guardado y hoja limpiada', 'type': 'success'}
        }

    # 2) limpiar campos “rellenables” (no tocar el link a repair.order)
    def _reset_record_fields(self, rec):
        vals = {}
        for fname, f in rec._fields.items():
            if fname in ('id','display_name','create_uid','create_date','write_uid','write_date'):
                continue
            if f.type == 'many2one' and getattr(f, 'comodel_name', '') == 'repair.order':
                continue
            if f.type in ('char','text','html','float','integer','boolean','date','datetime','selection','many2one','binary'):
                vals[fname] = False
        if vals:
            rec.sudo().write(vals)

    def _get_repair_order_manager_group(self):
        return self.env.ref("custom_repair_product.group_repair_manager")
    
    def _get_repair_order_user_group(self):
        return self.env.ref("custom_repair_product.group_repair_user")
    
    def _get_repair_order_access_all_groups(self):
        return self._get_repair_order_manager_group() | self._get_repair_order_user_group()
    
    def _get_repair_order_module_name(self):
        return "custom_repair_product"
