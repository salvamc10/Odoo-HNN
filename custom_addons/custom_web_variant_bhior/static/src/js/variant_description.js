/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { patch } from "@web/core/utils/patch";
import { WebsiteSale } from "@website_sale/js/website_sale";

patch(WebsiteSale.prototype, {
    async _getCombinationInfo(ev) {
        console.log('=== DEBUG _getCombinationInfo ===');
        console.log('Event:', ev);
        
        const result = await super._getCombinationInfo(ev);
        
        console.log('Result type:', typeof result);
        console.log('Result value:', result);
        console.log('Result is null:', result === null);
        console.log('Result is undefined:', result === undefined);
        
        if (result) {
            console.log('Result keys:', Object.keys(result));
            console.log('Has product_product:', 'product_product' in result);
        }
        
        console.log('=== END DEBUG ===');

        // Tu lógica original con verificaciones
        if (result && typeof result === 'object' && result.product_product) {
            const customDescription = document.getElementById('product_custom_description');
            if (customDescription) {
                const descriptionValue = result.product_product.x_studio_descripcion_1 || '';
                customDescription.innerHTML = descriptionValue;
            }
        }

        return result;
    }
});
