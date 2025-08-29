/* @odoo-module */

import {_t} from "@web/core/l10n/translation";
import {Chatter} from "@mail/chatter/web_portal/chatter";
import {patch} from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { use } from "react";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.ui = useService("ui");
        this.threadId = this.props.threadId;
        this.threadModel = this.props.threadModel;
        this.state = useState({
            ...this.state,
            favorite: false,
        });
        this.isFavorite ();
    },

    async onToggleFavorite() {
        const favorite = await this.isFavorite();
        if (favorite.length > 0) {
            if (favorite.length > 0) {
                this.state.favorite = false;
                await this.orm.unlink("my.favorite", favorite[0].id);

})