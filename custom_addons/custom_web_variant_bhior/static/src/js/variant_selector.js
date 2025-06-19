
// /** @odoo-module **/

console.log("TEST: Variant selector loaded successfully");

document.addEventListener('DOMContentLoaded', function() {
    console.log("TEST: DOM Content Loaded");
    
    var selects = document.querySelectorAll('select.js_variant_change');
    console.log("TEST: Found", selects.length, "variant selects");
    
    if (selects.length > 0) {
        console.log("TEST: First select:", selects[0]);
        selects[0].style.border = "2px solid red";
    }
});

// import { Component, onMounted } from "@odoo/owl";
// import { registry } from "@web/core/registry";

// export class VariantSelectorController extends Component {
//     setup() {
//         onMounted(() => {
//             this._insertPlaceholderOptions();
//             this._toggleAddToCartButton(false);
//         });
//     }

//     _insertPlaceholderOptions() {
//         const selects = this.el.querySelectorAll("select.variant_attribute");
//         selects.forEach(select => {
//             const hasEmpty = Array.from(select.options).some(opt => opt.value === "");
//             if (!hasEmpty) {
//                 const placeholder = new Option("--- Selecciona una opción ---", "", true, true);
//                 placeholder.disabled = true;
//                 select.insertBefore(placeholder, select.firstChild);
//                 select.value = "";
//             }

//             select.addEventListener("change", () => this._onVariantChanged());
//         });
//     }

//     _onVariantChanged() {
//         const selects = this.el.querySelectorAll("select.variant_attribute");
//         const allSelected = Array.from(selects).every(select => !!select.value);
//         this._toggleAddToCartButton(allSelected);
//     }

//     _toggleAddToCartButton(show) {
//         const button = this.el.querySelector("#add_to_cart, .a-submit");
//         if (button) {
//             button.style.display = show ? "" : "none";
//         }
//     }
// }

// registry.category("frontend_components").add("custom_variant_selector", {
//     component: VariantSelectorController,
//     selector: ".js_add_cart_variants",
// });

