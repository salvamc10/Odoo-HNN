/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class VariantSelector extends Component {
    static template = "my_module.VariantSelector";
    static props = { category: String };
    
    setup() {
        this.state = useState({
            selectedVariant: "",
            showAddToCart: false
        });
        
        this.onVariantChange = (ev) => {
            this.state.selectedVariant = ev.target.value;
            this.state.showAddToCart = !!this.state.selectedVariant;
        };
    }
}

registry.category("public_components").add("my_module.VariantSelector", VariantSelector);
