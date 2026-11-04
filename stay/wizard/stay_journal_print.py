# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# @author: Brother Irénée
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from babel.dates import format_date as babel_format_date

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, format_datetime


class StayJournalPrint(models.TransientModel):
    _name = "stay.journal.print"
    _description = "Print the Stay Lines"
    _rec_name = "date"

    date = fields.Date(required=True)
    date_label = fields.Char(compute="_compute_date_label")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    report_type = fields.Selection(
        [
            ("general", "General"),
            ("meal", "Meals"),
            ("arrival", "Arrivals"),
            ("fire", "Fire"),
        ],
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get("report_type") == "fire":
            date = fields.Date.context_today(self)
        else:
            date = fields.Date.context_today(self) + timedelta(1)
        res["date"] = date
        return res

    @api.depends("date")
    def _compute_date_label(self):
        for wiz in self:
            res = self.env["stay.date.label"]._get_date_label(self.date)
            wiz.date_label = res

    def print_journal(self):
        self.ensure_one()
        assert self.report_type
        method_name = f"print_journal_{self.report_type}"
        method = getattr(self, method_name)
        return method()

    def print_journal_general(self):
        lines = self.env["stay.line"].search(
            [
                ("date", "=", self.date),
                ("company_id", "=", self.company_id.id),
            ]
        )
        if not lines:
            raise UserError(
                _(
                    "There are no stays on %(date)s in company %(company)s.",
                    date=format_date(self.env, self.date),
                    company=self.company_id.display_name,
                )
            )
        action = (
            self.env.ref("stay.report_stay_journal_print")
            .with_context(discard_logo_check=True)
            .report_action(self)
        )
        return action

    def print_journal_meal(self):
        action = (
            self.env.ref("stay.report_stay_journal_meal")
            .with_context(discard_logo_check=True)
            .report_action(self)
        )
        return action

    def print_journal_arrival(self):
        action = (
            self.env.ref("stay.report_stay_journal_arrival")
            .with_context(discard_logo_check=True)
            .report_action(self)
        )
        return action

    def print_journal_fire(self):
        bad_rooms = self.env["stay.room"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("building_id", "=", False),
                ("fire_report_exclude", "=", False),
            ]
        )
        if bad_rooms:
            raise UserError(
                _(
                    "Rooms %s are not linked to a building.",
                    " ,".join([r.display_name for r in bad_rooms]),
                )
            )
        action = (
            self.env.ref("stay.report_stay_fire")
            .with_context(discard_logo_check=True)
            .report_action(self)
        )
        return action

    def get_report_by_refectory(self):
        """Method for the report (replace report parser)"""
        lines = self.env["stay.line"].search(
            [
                ("date", "=", self.date),
                ("company_id", "=", self.company_id.id),
            ]
        )
        res = {}
        # {refectory_obj1 : {
        #       'lunch_subtotal': 2,
        #       'dinner_subtotal': 4,
        #       'bed_night_subtotal': 5,
        #       'lines': [line1, line2, line3],
        #       }
        # }
        for line in lines:
            refectory = line.refectory_id
            if refectory in res:
                res[refectory]["breakfast_subtotal"] += line.breakfast_qty
                res[refectory]["lunch_subtotal"] += line.lunch_qty
                res[refectory]["picnic_lunch_subtotal"] += line.picnic_lunch_qty
                res[refectory]["dinner_subtotal"] += line.dinner_qty
                res[refectory]["bed_night_subtotal"] += line.bed_night_qty
                res[refectory]["lines"].append(line)
            else:
                res[refectory] = {
                    "breakfast_subtotal": line.breakfast_qty,
                    "lunch_subtotal": line.lunch_qty,
                    "picnic_lunch_subtotal": line.picnic_lunch_qty,
                    "dinner_subtotal": line.dinner_qty,
                    "bed_night_subtotal": line.bed_night_qty,
                    "lines": [line],
                }
        # print "res=", res.items()
        return res.items()

    def _report_move_date(self, date, move_type, raise_if_none=False):
        assert move_type in ("arrival", "departure")
        assert date
        sso = self.env["stay.stay"]
        stays = sso.search(
            [
                (move_type + "_date", "=", date),
                ("company_id", "=", self.company_id.id),
                ("state", "not in", ("draft", "cancel")),
            ]
        )
        if not stays and raise_if_none:
            if move_type == "arrival":
                raise UserError(_("No arrival on %s.") % format_date(self.env, date))
            elif move_type == "departure":
                raise UserError(_("No departure on %s.") % format_date(self.env, date))
        res = (
            stays.filtered(lambda x: x[move_type + "_time"] == "morning")
            + stays.filtered(lambda x: x[move_type + "_time"] == "afternoon")
            + stays.filtered(lambda x: x[move_type + "_time"] == "evening")
        )
        return res

    def _report_nomove(self, date):
        assert date
        sso = self.env["stay.stay"]
        stays = sso.search(
            [
                ("company_id", "=", self.company_id.id),
                ("arrival_date", "<", date),
                ("departure_date", ">", date),
                ("state", "not in", ("draft", "cancel")),
            ]
        )
        return stays

    def report_general_data(self):
        res = {}
        day = self.date
        self.env["stay.date.label"]._get_date_label(day)
        res[day] = {
            "date_label": babel_format_date(day, "full", locale="fr"),
            "ordo": self.env["stay.date.label"]._get_date_label(day) or "",
            "departure": self._report_move_date(day, "departure"),
            "arrival": self._report_move_date(day, "arrival"),
            "nomove": self._report_nomove(day),
        }
        nextday = day + timedelta(1)
        res[nextday] = {
            "date_label": babel_format_date(nextday, locale="fr", format="full"),
            "ordo": self.env["stay.date.label"]._get_date_label(nextday) or "",
            "departure": self._report_move_date(nextday, "departure"),
            "arrival": self._report_move_date(nextday, "arrival"),
            "nomove": self._report_nomove(nextday),
        }
        return res

    def report_arrival_data(self):
        return self._report_move_date(self.date, "arrival", raise_if_none=True)

    def report_date_formatted(self):
        return babel_format_date(self.date, "full", locale=self.env.user.lang)

    def report_edit_datetime(self):
        res = format_datetime(
            self.env, fields.Datetime.now(), lang_code=self.env.user.lang
        )
        return res

    def _report_fire_date_title(self):
        self.ensure_one()
        start_night_date = format_date(self.env, self.date)
        end_night_date = format_date(self.env, self.date + timedelta(1))
        return f"{start_night_date} → {end_night_date}"

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
                            ("construction", "=", False),
                        ]
                    )
                    guest_qty = sum([assign.guest_qty for assign in assigns])
                    res[building]["rooms"].append((room, assigns))
                    res[building]["total_guest_qty"] += guest_qty
        return res
