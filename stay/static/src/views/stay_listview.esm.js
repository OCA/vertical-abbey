import {ListRenderer} from "@web/views/list/list_renderer";
import {StayDashBoard} from "@stay/views/stay_dashboard.esm";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

export class StayDashBoardRenderer extends ListRenderer {
    static template = "stay.StayListView";
    static components = Object.assign({}, ListRenderer.components, {StayDashBoard});
}

export const StayDashBoardListView = {
    ...listView,
    Renderer: StayDashBoardRenderer,
};

registry.category("views").add("stay_dashboard_list", StayDashBoardListView);
