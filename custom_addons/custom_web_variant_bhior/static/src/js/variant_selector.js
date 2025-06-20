/** @odoo-module **/

console.log("Variant Selector: Module loaded successfully");

function initVariantSelector() {
    console.log("Variant Selector: Initializing...");
    
    var selects = document.querySelectorAll('select.js_variant_change');
    console.log("Variant Selector: Found", selects.length, "variant selects");
    
    if (selects.length === 0) {
        console.log("Variant Selector: No variant selects found, retrying in 500ms...");
        setTimeout(initVariantSelector, 500);
        return;
    }
    
    selects.forEach(function(select, index) {
        console.log("Variant Selector: Processing select", index + 1);
        
        // Quitar selección previa
        Array.from(select.options).forEach(function(option) {
            option.selected = false;

            // Añadir descripción si está en data-description
            const desc = option.dataset.description;
            if (desc && !option.textContent.includes(desc)) {
                option.textContent = `${option.textContent.trim()} - ${desc}`;
            }
        });
        
        // Verificar si ya existe una opción vacía
        var hasEmpty = Array.from(select.options).some(function(opt) {
            return opt.value === '' || opt.value === '0';
        });
        
        if (!hasEmpty) {
            var placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = '--- Selecciona una opción ---';
            placeholder.disabled = true;
            placeholder.selected = true;
            select.insertBefore(placeholder, select.firstChild);
            console.log("Variant Selector: Placeholder added to select", index + 1);
        } else {
            // Si ya existe una opción vacía, seleccionarla
            select.value = '';
            console.log("Variant Selector: Empty option already exists, selected it");
        }
        
        // Agregar event listener para cambios
        select.addEventListener('change', function(e) {
            const selects = document.querySelectorAll('select.js_variant_change');
            const allSelected = Array.from(selects).every(function(sel) {
                return sel.value && sel.value !== '' && sel.value !== '0';
            });

            if (!allSelected) {
                console.log("Variant Selector: Not all selected - hiding button");
                toggleAddToCartButton(false);
                // Limpiar descripción personalizada
                const customDescDiv = document.getElementById('product_custom_description');
                if (customDescDiv) {
                    customDescDiv.innerHTML = '';
                }
                return;
            }
                
            console.log("Variant Selector: Select changed, value:", this.value);
            handleVariantChange();
        });
    });
    
    // Ocultar botón inicialmente
    toggleAddToCartButton(false);
    console.log("Variant Selector: Initialization complete");
}

function handleVariantChange() {    
    const selects = document.querySelectorAll('select.js_variant_change');
    const allSelected = Array.from(selects).every(function(select) {
        const isSelected = select.value && select.value !== '' && select.value !== '0';
        console.log("Variant Selector: Select value:", select.value, "Selected:", isSelected);
        return isSelected;
    });

    toggleAddToCartButton(allSelected);

    if (!allSelected) return;

    const productTemplateId = document.querySelector('input[name="product_template_id"]')?.value;
    const combination_ids = Array.from(selects).map(select => parseInt(select.value)).filter(Boolean);

    console.log("Variant Selector: Template ID:", productTemplateId);
    console.log("Variant Selector: Combination IDs:", combination_ids);

    fetch("/website_sale/get_combination_info", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: {
                product_template_id: parseInt(productTemplateId),
                product_id: false,
                combination: combination_ids,
                only_template: false,
                add_qty: 1.0
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        const result = data.result;
        if (!result) {
            console.warn("Variant Selector: No combination info received");
            return;
        }

        const customDescDiv = document.getElementById('product_custom_description');
        if (customDescDiv && 'x_studio_descripcion_1' in result) {
            customDescDiv.innerHTML = result.x_studio_descripcion_1 || '';
            console.log("Variant Selector: Description updated from direct fetch");
        } else {
            console.warn("Variant Selector: x_studio_descripcion_1 not in result");
        }

       
    })
    .catch(err => {
        console.error("Variant Selector: Error fetching combination info:", err);
    });
}


function toggleAddToCartButton(show) {
    // Buscar diferentes posibles selectores para el botón
    var button = document.querySelector('#add_to_cart') || 
                 document.querySelector('.a-submit') ||
                 document.querySelector('button[type="submit"]') ||
                 document.querySelector('.btn-primary');
    
    if (button) {
        button.style.display = show ? '' : 'none';
        console.log("Variant Selector: Button", show ? 'shown' : 'hidden');
    }
}

// Ejecutar inmediatamente y también cuando el DOM esté listo
initVariantSelector();

// Backup: ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVariantSelector);
} else if (document.readyState === 'complete') {
    // DOM ya está listo, ejecutar inmediatamente
    setTimeout(initVariantSelector, 100);
}

document.body.addEventListener('update-product-info', function (e) {
    const data = e.detail?.combination_info;
    if (!data) return;

    if ('x_studio_descripcion_1' in data) {
        const customDescDiv = document.getElementById('product_custom_description');
        if (customDescDiv) {
            customDescDiv.innerHTML = data.x_studio_descripcion_1 || '';
            console.log("Variant Selector: Updated description from combination_info event");
        }
    }
});

// Observar cambios dinámicos en la página (para AJAX)
var observer = new MutationObserver(function(mutations) {
    var shouldReinit = false;
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            Array.from(mutation.addedNodes).forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    if (node.classList && node.classList.contains('js_variant_change')) {
                        shouldReinit = true;
                    } else if (node.querySelector && node.querySelector('.js_variant_change')) {
                        shouldReinit = true;
                    }
                }
            });
        }
    });
    
    if (shouldReinit) {
        console.log("Variant Selector: New variant selects detected, reinitializing...");
        setTimeout(initVariantSelector, 100);
    }
});

// Observar cambios en el documento
observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log("Variant Selector: All event listeners registered");