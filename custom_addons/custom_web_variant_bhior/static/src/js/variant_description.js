/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { patch } from "@web/core/utils/patch";
import { WebsiteSale } from "@website_sale/js/website_sale";

patch(WebsiteSale.prototype, {
    async _getCombinationInfo(ev) {
        const result = await super._getCombinationInfo(ev);

       const customDescription = document.getElementById('product_custom_description');
        const descriptionValue = result.product_product?.x_studio_descripcion_1;

        if (customDescription) {
            customDescription.innerHTML = descriptionValue ? descriptionValue : '';
        }

        return result;
    }
});
