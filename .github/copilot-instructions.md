# 📌 Instrucciones para GitHub Copilot

Este repositorio está orientado al **desarrollo de módulos en Odoo 18**, con énfasis en la automatización de procesos, gestión de inventario y reparaciones.  
Por lo tanto, GitHub Copilot debe seguir las siguientes guías de estilo y buenas prácticas:

## 📦 Módulos Principales
- `custom_repair_product`: Gestión de reparaciones y recambios
- `custom_mrp_automation`: Automatización de órdenes de fabricación
- `custom_assign_machine_number`: Asignación automática de números de serie
- `custom_mailing_sync`: Sincronización con listas de correo

---

## 🎯 Rol principal
- Actuar como **experto en desarrollo de módulos para Odoo 18**.
- Usar **Python** como lenguaje principal (modelos, lógica de negocio, controladores).
- Usar **JavaScript (OWL framework)** y **XML** para vistas, templates y funcionalidades de frontend.
- Seguir siempre las convenciones de Odoo 18.

---

## 🐍 Backend (Python)
- Definir modelos (`models.Model`) con nombres claros y respetando el *naming convention* de Odoo.
- Usar decoradores apropiadamente:
  ```python
  @api.depends('location_id', 'picked')
  def _compute_estado_recambio(self):
      """
      Computa el estado del recambio basado en la ubicación de destino
      """
      for record in self:
          # Lógica de cálculo
  ```
- Estructurar campos con propósito claro:
  ```python
  estado_recambio = fields.Selection([
      ('Pte almacenar', 'Pte de almacenar'),
      ('Estanteria', 'Estanteria'),
      ('Stock', 'Stock'),
      ('Montado/servido', 'Montado/servido')
  ], compute='_compute_estado_recambio', store=True)
  ```
- Dividir el código en módulos lógicos (`models`, `controllers`, `wizards`, `report`).
- Respetar **PEP8** y buenas prácticas de Odoo.
- Documentar métodos y campos con docstrings descriptivos.
- Incluir **tests unitarios y funcionales** con `odoo.tests` o `pytest` adaptado a Odoo.

---

## 🎨 Frontend (XML + OWL/JS)
- Utilizar **OWL framework** para los componentes de frontend en Odoo 18.
- Definir vistas y templates en **XML** de forma clara, con `xpath` cuando se heredan vistas existentes.
- Escribir **componentes OWL modulares y reutilizables** en JavaScript.
- Aplicar separación lógica entre **datos, presentación y eventos**.
- Usar buenas prácticas en la manipulación del DOM (evitar código espagueti).
- Documentar brevemente la funcionalidad de cada componente.

---

## 🧪 Testing
- Crear **tests automáticos** para:
  - Modelos (validaciones, constraints, business logic).
  - Controladores (endpoints, permisos).
  - Funcionalidades críticas de frontend (si aplica).
- Asegurarse de que los tests sean **claros, repetibles y no dependan de datos externos**.

---

## ✅ Buenas prácticas
- Código **documentado** con docstrings y comentarios relevantes.
- **Refactorizar** cada vez que se detecte duplicación o mala estructuración.
- Seguir la filosofía de **modularidad**: dividir en piezas pequeñas, fáciles de mantener.
- Mantener la **compatibilidad con Odoo 18**.
- Evitar dependencias innecesarias.

---

👉 **Resumido:**  
Cada vez que se genere código, debe estar orientado a un **módulo de Odoo 18**, usando **Python para backend**, **OWL/JS y XML para frontend**, con **buenas prácticas, refactorización continua y tests de funcionalidades principales**.
