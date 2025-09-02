# Instrucciones personalizadas para Copilot Chat

Configuración para trabajar con **Python**, el framework **OWL**, y utilizando **MCP de GitHub**.

---

## 📌 Lenguaje principal
- Todo el código debe generarse en **Python**.  
- Aplicar convenciones **PEP 8** (estilo, imports, nombres).  
- Incluir **type hints** y docstrings en todas las funciones y clases.  

---

## 📌 Framework: OWL
- Usar **OWL** como framework base.  
- Seguir patrones de diseño recomendados por OWL.  
- Estructurar el proyecto en módulos claros y mantenibles.  
- Cada nuevo componente debe incluir:
  - Docstring con propósito y ejemplos.
  - Manejo de errores.
  - Comentarios explicativos cuando la lógica sea compleja.  

---

## 📌 MCP (Model Context Protocol) – GitHub
- Utilizar **MCP de GitHub** para integraciones con repositorios.  
- Ejemplos deben incluir:
  - Conexión segura con autenticación.
  - Explicación breve de cada comando MCP usado.  
- Favorecer buenas prácticas en CI/CD y flujos de trabajo de repositorios.  

---

## 📌 Refactorización y buenas prácticas
- **Refactorizar siempre que sea posible**: simplificar código, eliminar duplicados, mejorar legibilidad.  
- Aplicar principios **SOLID** y **Clean Code**.  
- Promover modularidad y reutilización.  

---

## 📌 Testing
- Crear siempre **tests unitarios y de integración** con `pytest`.  
- Seguir la estructura:
  - `tests/unit/` para pruebas unitarias.
  - `tests/integration/` para pruebas de integración.  
- Cada nueva función o clase debe venir acompañada de al menos un test.  
- Usar mocks cuando sea necesario para desacoplar dependencias.  

---

## 📌 Revisión de código
- Verificar seguridad (manejo de credenciales, inyecciones, validaciones).  
- Verificar rendimiento (consultas innecesarias, complejidad).  
- Asegurar cumplimiento de PEP 8 y estándares OWL.  
- Recomendar mejoras de modularidad y cobertura de tests.  

---

## 📌 Estándares de commits y PRs
- **Commits** deben usar el formato:  
  `<tipo>(<área>): <descripción breve>`
  Ejemplo:  
    feat(api): agregar endpoint OWL para autenticación
    fix(core): corregir error en integración MCP

    
- **Pull Requests** deben incluir:
- Resumen del cambio
- Justificación
- Checklist de pruebas ejecutadas  

---

## 📌 Modos de chat sugeridos
1. **Modo Desarrollo OWL**  
 - Solo generar/modificar código Python con OWL.  

2. **Modo Refactorización**  
 - Revisar código existente, proponer mejoras, aplicar principios de buenas prácticas y refactorización continua.  

3. **Modo Testing**  
 - Generar tests unitarios e integración automáticamente para todo nuevo código.  

4. **Modo Integración MCP**  
 - Ayudar a configurar y extender el uso de MCP con GitHub y herramientas externas.  

    
## Arquitectura del Proyecto

- Cada carpeta en `/custom_addons` es un módulo independiente de Odoo
- Los módulos siguen la estructura estándar de Odoo:
  ```
  módulo/
    __init__.py
    __manifest__.py
    models/       # Modelos de datos
    views/        # Vistas XML 
    security/     # Permisos y reglas de acceso
    data/        # Datos XML
    static/      # Assets web (JS, CSS)
    ```

## Patrones Clave

1. **Manifiestos de Módulos**: Cada módulo tiene su `__manifest__.py` que define:
   - Dependencias (`depends`)
   - Datos a cargar (`data`) 
   - Assets web (`assets`)
   - Metadatos (nombre, versión, etc.)

2. **Convenciones de Código**:
   - Nombres de módulos inician con `custom_*`
   - Licencia estándar: LGPL-3
   - Los modelos heredan usando `_inherit`
   - Las vistas extienden usando `inherit_id`

3. **Flujos de Trabajo**:
   - Los módulos de reparación (repair) extienden la funcionalidad base de reparaciones
   - Los módulos de ventas personalizan flujos de documentación y secuencias
   - Los módulos de inventario manejan lotes y etiquetas

## Características Específicas

1. **Estado de Recambios**: 
   - Se calcula basado en ubicación y estado 'picked'
   - Estados posibles: Montado/servido, Pte almacenar, Stock, Estanteria
   - Ver: `custom_repair_product/models/stock_move.py`

2. **Integración Web**:
   - Los módulos web usan assets en `web.assets_frontend`
   - Las plantillas web van en `views/*.xml`

## Mejores Prácticas

1. **Campos Computados**:
   - Usar `@api.depends` en lugar de `@api.onchange` 
   - Especificar dependencias explícitamente
   - Considerar almacenamiento (`store=True`) cuando sea apropiado

2. **Vistas**:
   - Reutilizar grupos de campos existentes
   - Mantener herencia limpia usando xpath
   - Documentar cambios complejos en XML

3. **Seguridad**:
   - Definir reglas de acceso en `security/`
   - Usar grupos para control granular
   - Documentar permisos requeridos

## Tareas Comunes

1. **Nuevo Módulo**:
   ```python
   {
       'name': 'Nombre del Módulo',
       'version': '18.0.1.0',
       'license': 'LGPL-3',
       'depends': ['base'],
       'data': [],
       'installable': True,
   }
   ```

2. **Heredar un Modelo**:
   ```python
   class MiModelo(models.Model):
       _inherit = 'modelo.existente'
   ```

3. **Extender una Vista**:
   ```xml
   <record id="vista_heredada" model="ir.ui.view">
       <field name="inherit_id" ref="modulo.vista_original"/>
       <field name="arch" type="xml">
           <xpath expr="//field[@name='campo']" position="after">
               <field name="nuevo_campo"/>
           </xpath>
       </field>
   </record>
   ```
