/* @odoo-module */

import {_t} from "@web/core/l10n/translation";
import {Chatter} from "@mail/chatter/web_portal/chatter";
import {patch} from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


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
        if (favorite.length > 0)  {
            if (favorite.length > 0) {
                this.state.favorite = false;
                await this.orm.unlink("my.favorite", favorite[0].id);
            }
            this.notification.add(_t("Removed from favorites"), {
                type: "danger",
                sticky: false
            });

        } else {
            this.state.favorite = true;
            await this.orm.create("my.favorite", [
                {
                    user_id: this.env.model.config.context.uid,
                    res_model: this.threadModel,
                    res_id: this.threadId,
                },
            ]);
            this.notification.add(_t("Added to favorites"), {
                type: "success",
                sticky: true,                               
            });
        }
        this.ui.bus.trigger("UI-REFRESH-FAVORITE");
    },

    async isFavorite() {
        const favorite = await this.orm.searchRead(
            "my.favorite",
            [
                ["user_id", "=", this.env.model.config.context.uid],
                ["res_model", "=", this.threadModel],
                ["res_id", "=", this.threadId],
            ],
            ["id"]
        );
        this.state.favorite = favorite.length > 0;
        return favorite;
    },
});