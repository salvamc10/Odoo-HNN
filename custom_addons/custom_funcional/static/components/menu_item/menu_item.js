/* @odoo-module */
import {Component} from "@odoo/owl";

export class HistoryMenuItem extends Component {
    static props= {
        favorite:{
            type: Object,
            shape:{
                favorite_id: Number,
                name: String,
                res_id: Number ,
                res_model: String,
            },
        },
            onToggleFavorite: Function,
            onDeleteFavorite: Function,
        };
        static template = "custom_funcional.HistoryMenuItem";

        setup() {}

        onToggleFavorite(action_type) {
            this.props.onToggleFavorite(this.props.favorite, action_type);
        }

        onDeleteFavorite() {
            this.props.onDeleteFavorite(this.props.favorite.favorite_id);
        }
    }