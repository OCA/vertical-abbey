import {Component, onWillStart} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class StayDashBoard extends Component {
    static template = "stay.StayDashboard";
    static props = {};
    setup() {
        this.orm = useService("orm");

        onWillStart(async () => {
            this.stayData = await this.orm.call("stay.stay", "get_dashboard_data");
        });
    }
}
