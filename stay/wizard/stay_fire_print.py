# Copyright 2025 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class StayFirePrint(models.TransientModel):
    _name = "stay.fire.print"
    _description = "Print the Fire Report"
    _rec_name = "date"

    date = fields.Date(
        string="Date",
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    def run(self):
        self.ensure_one()
        bad_rooms = self.env["stay.room"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("building_id", "=", False),
                ("fire_report_exclude", "=", False),
            ]
        )
        if bad_rooms:
            raise UserError(
                _("Rooms %s are not linked to a building.")
                % " ,".join([r.display_name for r in bad_rooms])
            )
        action = (
            self.env.ref("stay.report_stay_fire")
            .with_context({"discard_logo_check": True})
            .report_action(self)
        )
        return action

    def _report_fire_data(self):
        buildings = self.env["stay.building"].search([])
        res = {}
        # key = building
        # value = {'total_guest_qty': 4, 'rooms': [(room, assign_multi_recordset)]}
        for building in buildings:
            rooms = self.env["stay.room"].search(
                [
                    ("building_id", "=", building.id),
                    ("company_id", "=", self.company_id.id),
                    ("fire_report_exclude", "=", False),
                ],
                order="fire_report_sequence, sequence, id",
            )
            if rooms:
                res[building] = {"total_guest_qty": 0, "rooms": []}
                for room in rooms:
                    assigns = self.env["stay.room.assign"].search(
                        [
                            ("arrival_date", "<=", self.date),
                            ("departure_date", ">", self.date),
                            ("room_id", "=", room.id),
                        ]
                    )
                    guest_qty = sum([assign.guest_qty for assign in assigns])
                    res[building]["rooms"].append((room, assigns))
                    res[building]["total_guest_qty"] += guest_qty
        return res

    def _report_edit_datetime(self):
        return self.env["stay.journal.print"].report_edit_datetime()

    def _report_date_title(self):
        self.ensure_one()
        start_night_date = format_date(self.env, self.date)
        end_night_date = format_date(self.env, self.date + timedelta(1))
        return f"{start_night_date} → {end_night_date}"
