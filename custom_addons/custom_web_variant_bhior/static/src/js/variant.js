/** @odoo-module **/

odoo.define('custom_web_variant_bhior.variant_selector', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const VariantMixin = require('website_sale.variant_mixin');

    publicWidget.registry.WebsiteSale.include({
        _onChangeCombination: function (ev, $parent, combination) {
            this._super.apply(this, arguments);

            // Si no hay combinación válida, ocultamos el botón
            if (!combination || !combination.product_id) {
                $('.js_main_product .a-submit').hide();
            } else {
                $('.js_main_product .a-submit').show();
            }
        },

        start: function () {
            const result = this._super.apply(this, arguments);

            // Inicialmente oculta el botón si no hay combinación válida
            if (!$("#product_variant_id").val()) {
                $('.js_main_product .a-submit').hide();
            }

            return result;
        }
    });
});
