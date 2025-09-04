import {DropdownItem} from '@web/core/dropdown/dropdown_item';
import {registry} from '@web/core/registry';
import {useBus, useService} from '@web/core/utils/hooks';
import {_t} from '@web/core/l10n/translation';
import {user} from '@web/core/user';
import {ConfirmationDialog} from '@web/core/confirmation_dialog/confirmation_dialog';
import {HistoryMenuItem} from '@custom_funcional/components/menu_item/menu_item';
import { Component, use } from 'react';

export class HistoryMenu extends Component {
    static components = {Dropdown, DropdownItem, HistoryMenuItem};
    static props = [];
    static template = 'custom_funcional.Menu';

    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.dialogService = useService('dialog');
        this.ui = useService('ui');
        this.userId = user.userId;
        this.state = useState({ favorites: [] });
        useBus(this.ui.bus, 'UI-REFRESH-FAVORITE', (event) => {
            this.getFavoritesData();
        });
        onWillStart(async () => {
            await this.getFavoritesData();
        });
    }

    existsFavorites() {
        return this.state.favorites.length > 0;
    }   

    async getFavoritesData() {
       const favorite_list = [];
       const favorites = await this.orm.searchRead('my.favorite', [['user_id', '=', this.userId], 
        ]);
        for (const favorite of favorites) {
            const record = await this.orm.read(favorite.res_model, [favorite.res_id], ['id','name']);
            favorite_list.push({
                name: record[0].name,
                res_model: favorite.res_model,
                res_id: favorite.res_id,
                favorite_id: favorite.id,
            });
        }
        this.state.favorites = favorite_list;
    }

    onToggleFavorite(favorite, action_type) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t("Favorites"),
            res_model: favorite.res_model,
            res_id: favorite.res_id,
            target: action_type,
            views: [[false, 'form']],
        });


    }

    async onDeleteFavorite(favorite) {
        this.dialogService.add(ConfirmationDialog, {
            
            body: _t("Are you sure you want to remove this item from your favorites?"),
            confirm: async () => {
                await this.orm.unlink("my.favorite", [favorite]);
                this.ui.bus.trigger("UI-REFRESH-FAVORITE");
            },
            cancel: () => {},
        });
    }
    }

    export const systrayHistory = { 
        Component: HistoryMenu,
    };

    registry.category('systray').add('custom_funcional.Menu', systrayHistory, { sequence: 101 });