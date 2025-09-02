/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted } from "@odoo/owl";

export class CompanySignatureField extends Component {
    setup() {
        this.orm = useService("orm");
        this.user = useService("user");
        
        onWillStart(async () => {
            // Cargar la firma inicial basada en la compañía actual
            await this.loadSignature();
        });

        // Suscribirse a cambios en la compañía actual
        onMounted(() => {
            this.env.bus.addEventListener('COMPANY_CHANGED', this.onCompanyChange.bind(this));
        });
    }

    async loadSignature() {
        try {
            // Obtener la firma específica para la compañía actual
            const signature = await this.orm.call(
                'user.company.signature',
                'search_read',
                [[
                    ['user_id', '=', this.user.userId],
                    ['company_id', '=', this.env.services.company.currentCompany.id]
                ]],
                ['signature']
            );

            if (signature && signature.length > 0) {
                // Actualizar el campo signature en el formulario
                await this.orm.write('res.users', [this.user.userId], {
                    'signature': signature[0].signature || ''
                });
            }
        } catch (error) {
            console.error('Error al cargar la firma:', error);
        }
    }

    async onCompanyChange(event) {
        await this.loadSignature();
    }
}

CompanySignatureField.template = 'custom_signature_mail_for_company.SignatureField';
CompanySignatureField.props = {
    value: { type: String, optional: true },
    readonly: { type: Boolean, optional: true },
};

registry.category("fields").add("company_signature", CompanySignatureField);
