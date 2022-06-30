# Copyright 2022 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Matthieu Dubois <dubois.matthieu@tutanota.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class StayMultiDuplicate(models.TransientModel):
    _name = "stay.multi.duplicate"
    _description = "Multi Stay Duplicate Wizard"

    stay_id = fields.Many2one("stay.stay", required=True, readonly=True)
    frequency = fields.Selection(
        [("weekly", "Weekly")], required=True, default="weekly"
    )
    start_date = fields.Date(required=True, default=fields.Date.context_today)
    end_date = fields.Date(required=True)
    create_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
        ],
        default="draft",
        required=True,
    )
    keep_notes = fields.Boolean(string="Keep Notes?")
    keep_assignments = fields.Boolean(string="Keep assignments?", default=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert self._context.get("active_model") == "stay.stay"
        res["stay_id"] = self._context.get("active_id")
        return res

    def _prepare_stay_copy(self, cur_arrival_date):
        content = {
            "arrival_date": cur_arrival_date,
            "departure_date": cur_arrival_date
            + (self.stay_id.departure_date - self.stay_id.arrival_date),
        }
        if self.keep_notes is False:
            content["departure_note"] = False
            content["arrival_note"] = False
            content["notes"] = False

        if not self.keep_assignments or self.create_state == "draft":
            content["room_assign_ids"] = False

        return content

    def run(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.start_date < today:
            raise UserError(
                _("The start date %s is in the past!")
                % (format_date(self.env, self.start_date))
            )
        if self.end_date <= self.start_date:
            raise UserError(
                _("The end date (%s) must be after the start_date (%s)!")
                % (
                    format_date(self.env, self.end_date),
                    format_date(self.env, self.start_date),
                )
            )
        freq2days = {
            "weekly": 7,
        }

        new_stay_ids = []
        cur_arrival_date = self.start_date

        while cur_arrival_date <= self.end_date:
            existing_stay = self.env["stay.stay"].search(
                [
                    ("company_id", "=", self.stay_id.company_id.id),
                    ("partner_id", "=", self.stay_id.partner_id.id),
                    ("arrival_date", "=", cur_arrival_date),
                ],
                limit=1,
            )
            if existing_stay:
                raise UserError(
                    _(
                        "A stay already exists for guest '%s' with arrival date %s (stay %s)."
                    )
                    % (
                        self.stay_id.partner_id.display_name,
                        format_date(self.env, cur_arrival_date),
                        existing_stay.name,
                    )
                )
            new_stay = self.stay_id.copy(self._prepare_stay_copy(cur_arrival_date))
            if self.create_state == "confirm":
                new_stay.draft2confirm()
            new_stay_ids.append(new_stay.id)
            cur_arrival_date += timedelta(days=freq2days[self.frequency])

        action = self.env["ir.actions.actions"]._for_xml_id("stay.stay_action")
        action["domain"] = [("id", "in", new_stay_ids)]
        return action
