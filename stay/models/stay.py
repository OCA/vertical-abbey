# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# @author: Brother Irénée
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict
from datetime import datetime
from textwrap import shorten

import pytz
from dateutil.relativedelta import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import format_date

logger = logging.getLogger(__name__)
UNKNOWN_ARRIVAL_HOUR = "09"
UNKNOWN_DEPARTURE_HOUR = "20"
UNKNOWN_MINUTES = "01"

TIMEDICT = {
    "morning": "09:00",
    "afternoon": "15:00",
    "evening": "20:00",
    # Update the code in _convert_to_date_and_time_selection if known hours
    # are changed
    "unknown_arrival": f"{UNKNOWN_ARRIVAL_HOUR}:{UNKNOWN_MINUTES}",
    "unknown_departure": f"{UNKNOWN_DEPARTURE_HOUR}:{UNKNOWN_MINUTES}",
}


class StayStay(models.Model):
    _name = "stay.stay"
    _description = "Guest Stay"
    # as we have the default filter "Current and Future Stays", it's better to have
    # arrival_date asc and not arrival_date desc
    _order = "arrival_date"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char(string="Stay Number", default="/", copy=False)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Guest",
        ondelete="restrict",
        help="If guest is anonymous, leave this field empty.",
    )
    partner_name = fields.Text(
        string="Guest Names",
        required=True,
        tracking=True,
        compute="_compute_partner_name",
        readonly=False,
        store=True,
    )
    guest_qty = fields.Integer(string="Guest Quantity", default=1, tracking=True)
    arrival_date = fields.Date(
        string="Arrival Date", required=True, tracking=True, index=True
    )
    arrival_time = fields.Selection(
        [
            ("morning", "Morning"),
            ("afternoon", "Afternoon"),
            ("evening", "Evening"),
            ("unknown", "Unknown"),
        ],
        string="Arrival Time",
        required=True,
        tracking=True,
    )
    arrival_datetime = fields.Datetime(
        compute="_compute_arrival_datetime",
        inverse="_inverse_arrival_datetime",
        store=True,
        string="Arrival Date and Time",
    )
    arrival_note = fields.Char(string="Arrival Note")
    departure_date = fields.Date(
        string="Departure Date", required=True, tracking=True, index=True
    )
    departure_time = fields.Selection(
        [
            ("morning", "Morning"),
            ("afternoon", "Afternoon"),
            ("evening", "Evening"),
            ("unknown", "Unknown"),
        ],
        string="Departure Time",
        required=True,
        tracking=True,
    )
    departure_datetime = fields.Datetime(
        compute="_compute_departure_datetime",
        inverse="_inverse_departure_datetime",
        store=True,
        string="Departure Date and Time",
    )
    departure_note = fields.Char(string="Departure Note")
    notes = fields.Text()
    room_assign_ids = fields.One2many(
        "stay.room.assign",
        "stay_id",
        string="Room Assignments",
        states={"cancel": [("readonly", True)]},
        copy=False,
    )
    # Here, group_id is not a related of room, because we want to be able
    # to first set the group and later set the room
    group_id = fields.Many2one(
        "stay.group",
        string="Group",
        tracking=True,
        copy=False,
        domain="[('company_id', '=', company_id)]",
        ondelete="restrict",
        check_company=True,
        default=lambda self: self.env.user.context_stay_group_id.id or False,
    )
    # to workaround the bug https://github.com/OCA/web/issues/1446
    # in v12+, if this PR is merged https://github.com/OCA/web/issues/1446
    # the we could use color_field
    line_ids = fields.One2many(
        "stay.line",
        "stay_id",
        string="Stay Lines",
        states={"draft": [("readonly", True)], "cancel": [("readonly", True)]},
    )
    refectory_id = fields.Many2one(
        "stay.refectory",
        compute="_compute_refectory_id",
        store=True,
        readonly=False,
        string="Refectory",
        check_company=True,
    )
    no_meals = fields.Boolean(
        compute="_compute_refectory_id",
        store=True,
        readonly=False,
        string="No Meals",
        tracking=True,
        help="The stay lines generated from this stay will not have "
        "breakfast/lunch/dinner by default.",
    )
    construction = fields.Boolean()
    rooms_display_name = fields.Char(
        compute="_compute_room_assignment", string="Rooms", store=True
    )
    assign_status = fields.Selection(
        [
            ("none", "Waiting Assignation"),
            ("no_night", "No Nights"),
            ("partial", "Partial"),
            ("assigned", "Assigned"),
            ("over-assigned", "Over Assigned"),
            ("error", "Error"),
        ],
        string="Assign Status",
        compute="_compute_room_assignment",
        store=True,
    )
    guest_qty_to_assign = fields.Integer(compute="_compute_room_assignment", store=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("current", "Current"),
            ("done", "Finished"),
            ("cancel", "Cancelled"),
        ],
        readonly=True,
        default="draft",
        tracking=True,
        copy=False,
    )
    tag_ids = fields.Many2many("stay.tag", string="Tags")
    # for filter
    my_stay_group = fields.Boolean(
        compute="_compute_my_stay_group", search="_search_my_stay_group"
    )
    same_time_preceding_stay_id = fields.Many2one(
        "stay.stay",
        compute="_compute_preceding_next_stay_id",
        string="Preceding Stay which leaves on same time slot",
        help="Preceding stay which leaves on the same time slot in the same room(s)",
    )
    clash_time_preceding_stay_id = fields.Many2one(
        "stay.stay",
        compute="_compute_preceding_next_stay_id",
        string="Preceding Stay which leaves later",
        help="Preceding stay which leaves later that the arrival in the same room(s)",
    )
    same_time_next_stay_id = fields.Many2one(
        "stay.stay",
        compute="_compute_preceding_next_stay_id",
        string="Next Stay which arrives on same time slot",
        help="Next stay which arrives on the same time slot in the same room(s)",
    )
    clash_time_next_stay_id = fields.Many2one(
        "stay.stay",
        compute="_compute_preceding_next_stay_id",
        string="Next Stay which arrives before",
        help="Next stay which arrives before the departure in the same room(s)",
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique(name, company_id)",
            "A stay with this number already exists for this company.",
        ),
        (
            "guest_qty_positive",
            "CHECK(guest_qty > 0)",
            "The guest quantity must be positive.",
        ),
    ]

    @api.depends(
        "room_assign_ids.guest_qty",
        "room_assign_ids.room_id",
        "departure_date",
        "arrival_date",
        "guest_qty",
        "state",
    )
    def _compute_room_assignment(self):
        for stay in self:
            guest_qty_to_assign = stay.guest_qty
            room_codes = []
            for assign in stay.room_assign_ids:
                if assign.room_id:
                    guest_qty_to_assign -= assign.guest_qty
                    room_codes.append(assign.room_id.code or assign.room_id.name)
            if room_codes:
                rooms_display_name = ", ".join(room_codes)
            else:
                rooms_display_name = "\u2205"

            if stay.state == "cancel":
                assign_status = False
            elif not guest_qty_to_assign:
                assign_status = "assigned"
            elif stay.arrival_date == stay.departure_date:
                assign_status = "no_night"
            elif guest_qty_to_assign == stay.guest_qty:
                assign_status = "none"
            elif guest_qty_to_assign > 0:
                assign_status = "partial"
            elif guest_qty_to_assign < 0:
                assign_status = "over-assigned"
            else:
                assign_status = "error"
            stay.assign_status = assign_status
            stay.guest_qty_to_assign = guest_qty_to_assign
            stay.rooms_display_name = rooms_display_name

    @api.depends("partner_id")
    def _compute_partner_name(self):
        for stay in self:
            partner_name = False
            if stay.partner_id:
                partner_name = stay.partner_id._stay_get_partner_name()
            stay.partner_name = partner_name

    @api.depends("group_id")
    def _compute_refectory_id(self):
        for stay in self:
            refectory_id = False
            if stay.group_id and stay.group_id.default_refectory_id:
                refectory_id = stay.group_id.default_refectory_id.id
            elif stay.company_id.default_refectory_id:
                refectory_id = stay.company_id.default_refectory_id.id
            stay.refectory_id = refectory_id
            if stay.group_id:
                stay.no_meals = stay.group_id.default_no_meals

    @api.depends_context("uid")
    @api.depends("group_id")
    def _compute_my_stay_group(self):
        for stay in self:
            my_stay_group = False
            if (
                self.env.user.context_stay_group_id
                and stay.group_id == self.env.user.context_stay_group_id
            ):
                my_stay_group = True
            stay.my_stay_group = my_stay_group

    def _search_my_stay_group(self, operator, value):
        if self.env.user.context_stay_group_id:
            if operator == "=" and value:
                return [("group_id", "=", self.env.user.context_stay_group_id.id)]
            else:
                return [("group_id", "!=", self.env.user.context_stay_group_id.id)]
        else:
            return []

    @api.depends(
        "arrival_time",
        "arrival_date",
        "departure_date",
        "departure_time",
        "room_assign_ids.room_id",
    )
    def _compute_preceding_next_stay_id(self):
        for stay in self:
            clash_time_preceding_stay_id = False
            same_time_preceding_stay_id = False
            clash_time_next_stay_id = False
            same_time_next_stay_id = False
            room_ids = stay.room_assign_ids.room_id.ids
            base_domain = [
                ("room_id", "in", room_ids),
                ("company_id", "=", stay.company_id.id),
                ("state", "in", ("draft", "confirm", "current")),
                ("stay_id", "not in", (False, stay.id)),
            ]
            preceding_domain = base_domain + [
                ("departure_date", "=", stay.arrival_date)
            ]
            next_domain = base_domain + [("arrival_date", "=", stay.departure_date)]
            # PRECEDING
            if stay.arrival_time == "morning":
                preceding_clash_domain = preceding_domain + [
                    ("departure_time", "in", ("afternoon", "evening"))
                ]
            elif stay.arrival_time == "afternoon":
                preceding_clash_domain = preceding_domain + [
                    ("departure_time", "=", "evening")
                ]
            else:
                preceding_clash_domain = None
            if preceding_clash_domain:
                preceding_clash_assign = self.env["stay.room.assign"].search(
                    preceding_clash_domain, limit=1
                )
                if preceding_clash_assign:
                    clash_time_preceding_stay_id = preceding_clash_assign.stay_id.id
            preceding_same_time_assign = self.env["stay.room.assign"].search(
                preceding_domain + [("departure_time", "=", stay.arrival_time)], limit=1
            )
            if preceding_same_time_assign:
                same_time_preceding_stay_id = preceding_same_time_assign.stay_id.id
            # NEXT
            if stay.departure_time == "evening":
                next_clash_domain = next_domain + [
                    ("arrival_time", "in", ("morning", "afternoon"))
                ]
            elif stay.departure_time == "afternoon":
                next_clash_domain = next_domain + [("arrival_time", "=", "morning")]
            else:
                next_clash_domain = None
            if next_clash_domain:
                next_clash_assign = self.env["stay.room.assign"].search(
                    next_clash_domain, limit=1
                )
                if next_clash_assign:
                    clash_time_next_stay_id = next_clash_assign.stay_id.id
            next_same_time_assign = self.env["stay.room.assign"].search(
                next_domain + [("arrival_time", "=", stay.departure_time)], limit=1
            )
            if next_same_time_assign:
                same_time_next_stay_id = next_same_time_assign.stay_id.id

            stay.clash_time_preceding_stay_id = clash_time_preceding_stay_id
            stay.same_time_preceding_stay_id = same_time_preceding_stay_id
            stay.clash_time_next_stay_id = clash_time_next_stay_id
            stay.same_time_next_stay_id = same_time_next_stay_id

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("stay.stay")
        return super().create(vals)

    @api.model
    def _convert_to_datetime_naive_utc(self, date, time_sel):
        # Convert from local time to datetime naive UTC
        datetime_str = "%s %s" % (date, TIMEDICT[time_sel])
        datetime_naive = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        admin_user = self.env["res.users"].browse(SUPERUSER_ID)
        if admin_user.tz:
            logger.debug(
                "The timezone of admin user (ID %d) is %s", SUPERUSER_ID, admin_user.tz
            )
            admin_tz = pytz.timezone(admin_user.tz)
        else:
            logger.warning("The timezone of admin user (ID %d) is empty!", SUPERUSER_ID)
            admin_tz = pytz.utc
        datetime_aware_admin_tz = admin_tz.localize(datetime_naive)
        datetime_aware_utc = datetime_aware_admin_tz.astimezone(pytz.utc)
        datetime_naive_utc = datetime_aware_utc.replace(tzinfo=None)
        return datetime_naive_utc

    @api.model
    def _convert_to_date_and_time_selection(self, date_naive_utc):
        # Convert from datetime naive UTC to local time
        date_aware_utc = pytz.utc.localize(date_naive_utc)
        tz = pytz.timezone(self.env.user.tz)
        date_aware_local = date_aware_utc.astimezone(tz)
        if date_aware_utc.hour == int(
            UNKNOWN_ARRIVAL_HOUR
        ) and date_aware_utc.minute == int(UNKNOWN_MINUTES):
            time_selection = "unknown"
        elif date_aware_utc.hour == int(
            UNKNOWN_DEPARTURE_HOUR
        ) and date_aware_utc.minute == int(UNKNOWN_MINUTES):
            time_selection = "unknown"
        elif date_aware_local.hour < 12:
            time_selection = "morning"
        elif date_aware_local.hour < 18:
            time_selection = "afternoon"
        else:
            time_selection = "evening"
        return date_aware_local.date(), time_selection

    @api.depends("arrival_date", "arrival_time")
    def _compute_arrival_datetime(self):
        for stay in self:
            datetime_naive_utc = False
            if stay.arrival_date and stay.arrival_time:
                arrival_time = stay.arrival_time
                if arrival_time == "unknown":
                    arrival_time = "unknown_arrival"
                datetime_naive_utc = self._convert_to_datetime_naive_utc(
                    stay.arrival_date, arrival_time
                )
            stay.arrival_datetime = datetime_naive_utc

    @api.depends("departure_date", "departure_time")
    def _compute_departure_datetime(self):
        for stay in self:
            datetime_naive_utc = False
            if stay.departure_date and stay.departure_time:
                departure_time = stay.departure_time
                if departure_time == "unknown":
                    departure_time = "unknown_departure"
                datetime_naive_utc = self._convert_to_datetime_naive_utc(
                    stay.departure_date, departure_time
                )
            stay.departure_datetime = datetime_naive_utc

    # Used for the calendar view
    @api.onchange("departure_datetime")
    def _inverse_departure_datetime(self):
        for stay in self:
            if stay.departure_datetime:
                (
                    departure_date,
                    departure_time,
                ) = self._convert_to_date_and_time_selection(stay.departure_datetime)
                stay.departure_date = departure_date
                self.departure_time = departure_time

    @api.onchange("arrival_datetime")
    def _inverse_arrival_datetime(self):
        for stay in self:
            if stay.arrival_datetime:
                arrival_date, arrival_time = self._convert_to_date_and_time_selection(
                    stay.arrival_datetime
                )
                stay.arrival_date = arrival_date
                stay.arrival_time = arrival_time

    @api.onchange("arrival_date")
    def arrival_date_change(self):
        if self.arrival_date and (
            not self.departure_date or self.departure_date < self.arrival_date
        ):
            self.departure_date = self.arrival_date

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get("construction"):
            res.update(
                {
                    "partner_name": _("CONSTRUCTION"),
                    "arrival_time": "morning",
                    "departure_time": "evening",
                    "state": "confirm",
                }
            )
        return res

    @api.constrains(
        "departure_date",
        "departure_time",
        "arrival_date",
        "arrival_time",
        "room_assign_ids",
        "group_id",
        "guest_qty",
        "state",
    )
    def _check_stay(self):
        for stay in self:
            if stay.arrival_time == "unknown" and stay.state not in ("draft", "cancel"):
                raise ValidationError(
                    _(
                        "Arrival time cannot be set to unknown "
                        "if the stay is confirmed!"
                    )
                )
            if stay.departure_time == "unknown" and stay.state not in (
                "draft",
                "cancel",
            ):
                raise ValidationError(
                    _(
                        "Departure Time cannot be set to unknown if the stay is "
                        "confirmed."
                    )
                )
            if stay.arrival_date > stay.departure_date:
                raise ValidationError(
                    _("Arrival date (%s) cannot be after " "departure date (%s)!")
                    % (
                        format_date(self.env, stay.arrival_date),
                        format_date(self.env, stay.departure_date),
                    )
                )
            if stay.arrival_date == stay.departure_date:
                if stay.departure_time == "morning":
                    raise ValidationError(
                        _(
                            "For a stay without night, the departure time "
                            "can only be afternoon or evening."
                        )
                    )
                elif (
                    stay.departure_time == "afternoon"
                    and stay.arrival_time != "morning"
                ):
                    raise ValidationError(
                        _(
                            "For a stay without night, when the departure time "
                            "is afternoon, the arrival time must be morning."
                        )
                    )
                elif stay.departure_time == "evening" and stay.arrival_time not in (
                    "morning",
                    "afternoon",
                ):
                    raise ValidationError(
                        _(
                            "For a stay without night, when the departure time "
                            "is evening, the arrival time must be morning "
                            "or afternoon."
                        )
                    )
            if stay.room_assign_ids:
                group2room = {}
                # Only one loop on rooms, to improve perfs
                for room_assign in stay.room_assign_ids:
                    if room_assign.room_id.group_id:
                        group2room[room_assign.room_id.group_id] = room_assign.room_id
                if stay.group_id:
                    for group, room in group2room.items():
                        if group != stay.group_id:
                            raise ValidationError(
                                _(
                                    "Stay '%s' is linked to group '%s', but the "
                                    "room '%s' is linked to group '%s'."
                                )
                                % (
                                    stay.display_name,
                                    stay.group_id.display_name,
                                    room.display_name,
                                    group.display_name,
                                )
                            )

    @api.depends("partner_name", "name", "rooms_display_name", "state")
    def name_get(self):
        res = []
        state2label = dict(self.fields_get("state", "selection")["state"]["selection"])
        for stay in self:
            state = state2label.get(stay.state)
            short_partner_name = shorten(stay.partner_name, 35)
            if self._context.get("stay_name_get_partner_name"):
                name = "%s, %s" % (short_partner_name, state)
            elif self._context.get("stay_name_get_partner_name_qty"):
                name = "%s (%d), %s" % (short_partner_name, stay.guest_qty, state)
            elif self._context.get("stay_name_get_partner_name_qty_room"):
                name = "%s (%d)" % (short_partner_name, stay.guest_qty)
                if stay.rooms_display_name:
                    name += " [%s]" % stay.rooms_display_name
                name += ", %s" % state
            else:
                name = "%s, %s" % (stay.name, state)
            res.append((stay.id, name))
        return res

    def _prepare_stay_line(self, date):  # noqa: C901
        self.ensure_one()
        refectory_id = False
        if self.refectory_id:
            refectory_id = self.refectory_id.id
        elif self.group_id and self.group_id.default_refectory_id:
            refectory_id = self.group_id.default_refectory_id.id
        elif self.company_id.default_refectory_id:
            refectory_id = self.company_id.default_refectory_id.id
        vals = {
            "date": date,
            "stay_id": self.id,
            "partner_id": self.partner_id.id,
            "partner_name": self.partner_name,
            "refectory_id": refectory_id,
            "company_id": self.company_id.id,
            "breakfast_qty": 0,
            "lunch_qty": 0,
            "dinner_qty": 0,
            "bed_night_qty": 0,
        }
        if date == self.arrival_date and date == self.departure_date:
            if self.arrival_time == "morning":
                # then departure_time is afternoon or evening
                vals["lunch_qty"] = self.guest_qty
                if self.departure_time == "evening":
                    vals["dinner_qty"] = self.guest_qty
            elif self.arrival_time == "afternoon":
                # then departure_time is evening
                vals["dinner_qty"] = self.guest_qty
        elif date == self.arrival_date:
            vals["bed_night_qty"] = self.guest_qty
            if self.arrival_time == "morning":
                vals["lunch_qty"] = self.guest_qty
                vals["dinner_qty"] = self.guest_qty
            elif self.arrival_time == "afternoon":
                vals["dinner_qty"] = self.guest_qty
        elif date == self.departure_date:
            vals["breakfast_qty"] = self.guest_qty
            if self.departure_time == "morning":
                # When 'Manage breakfast' is not enable, we avoid to generate
                # a stay line for the last day if they leave in the morning
                if not self.env.user.has_group("stay.group_stay_breakfast"):
                    return {}
            elif self.departure_time == "afternoon":
                vals["lunch_qty"] = self.guest_qty
            elif self.departure_time == "evening":
                vals["lunch_qty"] = self.guest_qty
                vals["dinner_qty"] = self.guest_qty
        else:
            vals.update(
                {
                    "breakfast_qty": self.guest_qty,
                    "lunch_qty": self.guest_qty,
                    "dinner_qty": self.guest_qty,
                    "bed_night_qty": self.guest_qty,
                }
            )
        if self.no_meals:
            vals.update(
                {
                    "breakfast_qty": 0,
                    "lunch_qty": 0,
                    "dinner_qty": 0,
                }
            )
        return vals

    def _update_lines(self, previous_vals=None):
        self.ensure_one()
        if self.construction:
            return

        slo = self.env["stay.line"]
        if previous_vals:
            domain = [("stay_id", "=", self.id)]
            if (
                previous_vals["guest_qty"] == self.guest_qty
                and previous_vals["no_meals"] == self.no_meals
            ):
                # delete dates out of scope
                domain_dates = expression.OR(
                    [
                        [("date", "<", self.arrival_date)],
                        [("date", ">", self.departure_date)],
                    ]
                )
                # if arrival_date or time has changed, also delete old arrival line
                if (
                    previous_vals["arrival_date"] != self.arrival_date
                    or previous_vals["arrival_time"] != self.arrival_time
                ):
                    # delete old and new arrival date
                    domain_dates = expression.OR(
                        [
                            domain_dates,
                            [("date", "=", self.arrival_date)],
                            [("date", "=", previous_vals["arrival_date"])],
                        ]
                    )
                # if departure_date has changed, also delete old departure line
                if (
                    previous_vals["departure_date"] != self.departure_date
                    or previous_vals["departure_time"] != self.departure_time
                ):
                    domain_dates = expression.OR(
                        [
                            domain_dates,
                            [("date", "=", self.departure_date)],
                            [("date", "=", previous_vals["departure_date"])],
                        ]
                    )
                domain = expression.AND([domain, domain_dates])
            lines_to_delete = slo.search(domain)
            lines_to_delete.unlink()

        date = self.arrival_date
        existing_dates = [line.date for line in self.line_ids]
        while date <= self.departure_date:
            if date not in existing_dates:
                vals = self._prepare_stay_line(date)
                if vals:
                    slo.create(vals)
            date += relativedelta(days=1)

    def write(self, vals):
        stay2previous_vals = {}
        if not self._context.get("stay_no_auto_update"):
            for stay in self:
                if stay.line_ids:
                    stay2previous_vals[stay.id] = {
                        "arrival_date": stay.arrival_date,
                        "arrival_time": stay.arrival_time,
                        "departure_date": stay.departure_date,
                        "departure_time": stay.departure_time,
                        "guest_qty": stay.guest_qty,
                        "no_meals": stay.no_meals,
                    }
        res = super().write(vals)
        if not self._context.get("stay_no_auto_update"):
            today = fields.Date.context_today(self)
            for stay in self:
                if stay.state not in ("draft", "cancel"):
                    stay._update_lines(stay2previous_vals.get(stay.id))
                    stay._update_state(today)
        return res

    def _prepare_to_clean_info(self):
        self.ensure_one()
        to_clean = "%s %s (%d)" % (
            self.name,
            shorten(self.partner_name, 35),
            self.guest_qty,
        )
        return to_clean

    def _set_to_clean(self):
        for stay in self:
            for aline in stay.room_assign_ids:
                aline.room_id.write({"to_clean": stay._prepare_to_clean_info()})

    def _update_state(self, today):
        self.ensure_one()
        if self.state in ("confirm", "current") and self.departure_date < today:
            self.with_context(stay_no_auto_update=True).write({"state": "done"})
            self._set_to_clean()
        elif (
            self.state == "confirm"
            and self.arrival_date <= today
            and self.departure_date >= today
        ):
            self.with_context(stay_no_auto_update=True).write({"state": "current"})
        elif self.state in ("current", "done") and self.arrival_date > today:
            self.with_context(stay_no_auto_update=True).write({"state": "confirm"})

    # No need to call update_state() nor _update_lines() upon create
    # because stays are always created as draft

    def unlink(self):
        for stay in self:
            if stay.state not in ("draft", "cancel"):
                raise UserError(
                    _("You cannot delete stay '%s': you must cancel it first.")
                    % stay.display_name
                )
        return super().unlink()

    def draft2confirm(self):
        self.ensure_one()
        assert self.state == "draft"
        assert not self.line_ids
        self.write({"state": "confirm"})
        # write() will generate the stay lines

    def cancel(self):
        self.ensure_one()
        self.room_assign_ids.unlink()
        self.line_ids.unlink()
        self.with_context(stay_no_auto_update=True).write({"state": "cancel"})

    def cancel2draft(self):
        self.ensure_one()
        assert self.state == "cancel"
        self.room_assign_ids.unlink()
        self.line_ids.unlink()
        self.with_context(stay_no_auto_update=True).write({"state": "draft"})

    def guest_has_left(self):
        today = fields.Date.context_today(self)
        for stay in self:
            if stay.state != "current":
                raise UserError(
                    _("Stay '%s' is not in 'Current' state.") % stay.display_name
                )
            vals = {"state": "done"}
            if stay.departure_date > today:
                vals["departure_date"] = today
                stay.message_post(body=_("Guest has left before the end of his stay."))
            stay.write(vals)
            stay._set_to_clean()

    @api.model
    def _cron_stay_state_update(self):
        logger.info("Start Cron stay state update")
        today_dt = fields.Date.context_today(self)
        to_done = self.search(
            [("state", "in", ("confirm", "current")), ("departure_date", "<", today_dt)]
        )
        to_done.with_context(stay_no_auto_update=True).write({"state": "done"})
        to_done._set_to_clean()
        to_current = self.search(
            [
                ("state", "=", "confirm"),
                ("arrival_date", "<=", today_dt),
                ("departure_date", ">=", today_dt),
            ]
        )
        to_current.with_context(stay_no_auto_update=True).write({"state": "current"})
        to_cancel = self.search(
            [("state", "=", "draft"), ("departure_date", "<", today_dt)]
        )
        to_cancel.write({"state": "cancel"})
        logger.info("End cron stay state update")

    def _get_assign_base_conflict_domain(self):
        self.ensure_one()
        room_transition = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("stay.room_transition", default="one_empty_period")
        )
        logger.debug("room_transition is %s", room_transition)
        # No conflict IF :
        # leaves before my arrival (or same day)
        # OR arrivers after my departure (or same day)
        # CONTRARY :
        # leaves after my arrival
        # AND arrives before my departure
        # I use self.stay_id.arrival_datetime instead of self.arrival_datetime
        # because self.arrival_datetime may not be recomputed yet
        if room_transition in ("one_empty_period", "immediate"):
            equal = room_transition == "one_empty_period" and "=" or ""
            conflict_domain = [
                ("departure_datetime", f">{equal}", self.arrival_datetime),
                ("arrival_datetime", f"<{equal}", self.departure_datetime),
            ]
        elif room_transition == "night":
            conflict_domain = [
                ("departure_date", ">", self.arrival_date),
                ("arrival_date", "<", self.departure_date),
            ]
        else:
            raise UserError(
                _("Wrong value for config parameter 'stay.room_transition'.")
            )
        return conflict_domain

    def stay_notify_selection_button(self):
        assert self._context.get("active_ids")
        stays = self.browse(self._context["active_ids"])
        time2label = dict(
            self.fields_get("arrival_time", "selection")["arrival_time"]["selection"]
        )
        stay_list = [
            {
                "partner_name": stay.partner_name,
                "guest_qty": stay.guest_qty,
                "arrival_date": stay.arrival_date,
                "arrival_time": time2label[stay.arrival_time],
                "arrival_note": stay.arrival_note or "",
                "departure_date": stay.departure_date,
                "departure_time": time2label[stay.departure_time],
                "departure_note": stay.departure_note or "",
                "notes": stay.notes or "",
                "rooms": stay.rooms_display_name,
            }
            for stay in stays
        ]
        company = self.env.company
        ctx = {
            "default_model": "res.company",
            "default_res_id": company.id,
            "default_use_template": True,
            "default_template_id": self.env.ref("stay.stay_notify_selection").id,
            "default_composition_mode": "comment",
            "mark_so_as_sent": True,
            "custom_layout": "mail.mail_notification_paynow",
            "force_email": True,
            "stay_list": stay_list,
        }
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "target": "new",
            "context": ctx,
        }
        return action


class StayRoomAssign(models.Model):
    _name = "stay.room.assign"
    _description = "Room assignments"
    _check_company_auto = True

    stay_id = fields.Many2one("stay.stay", ondelete="cascade", index=True)
    room_id = fields.Many2one(
        "stay.room",
        required=True,
        ondelete="restrict",
        index=True,
        check_company=True,
        domain="[('id', 'not in', conflict_room_ids), ('company_id', '=', company_id), "
        "('group_id', 'in', (False, stay_group_id))]",
    )
    active = fields.Boolean(related="room_id.active", store=True)
    conflict_room_ids = fields.Many2many(
        "stay.room", compute="_compute_conflict_room_ids", string="Conflict Rooms"
    )
    guest_qty = fields.Integer(string="Guest Quantity", required=True)
    # Related fields
    group_id = fields.Many2one(related="room_id.group_id", store=True)
    stay_group_id = fields.Many2one(
        related="stay_id.group_id", store=True, string="Stay Group"
    )
    state = fields.Selection(related="stay_id.state", store=True)
    tag_ids = fields.Many2many(related="stay_id.tag_ids", readonly=False)
    arrival_date = fields.Date(
        related="stay_id.arrival_date", store=True, readonly=False
    )
    arrival_time = fields.Selection(
        related="stay_id.arrival_time", store=True, readonly=False
    )
    arrival_datetime = fields.Datetime(related="stay_id.arrival_datetime", store=True)
    arrival_note = fields.Char(
        related="stay_id.arrival_note", store=True, readonly=False
    )
    departure_date = fields.Date(
        related="stay_id.departure_date", store=True, readonly=False
    )
    departure_time = fields.Selection(
        related="stay_id.departure_time", store=True, readonly=False
    )
    departure_datetime = fields.Datetime(
        related="stay_id.departure_datetime", store=True
    )
    departure_note = fields.Char(
        related="stay_id.departure_note", store=True, readonly=False
    )
    notes = fields.Text(related="stay_id.notes", store=True, readonly=False)
    partner_id = fields.Many2one(related="stay_id.partner_id", store=True)
    partner_name = fields.Text(related="stay_id.partner_name", store=True)
    company_id = fields.Many2one(related="stay_id.company_id", store=True)
    # for filter
    my_stay_group = fields.Boolean(
        compute="_compute_my_stay_group", search="_search_my_stay_group"
    )

    _sql_constraints = [
        (
            "guest_qty_positive",
            "CHECK(guest_qty > 0)",
            "The guest quantity must be positive.",
        ),
        (
            "stay_room_unique",
            "unique(stay_id, room_id)",
            "This room has already been used in this stay.",
        ),
    ]

    @api.depends_context("uid")
    @api.depends("group_id")
    def _compute_my_stay_group(self):
        for assign in self:
            my_stay_group = False
            if (
                self.env.user.context_stay_group_id
                and assign.group_id == self.env.user.context_stay_group_id
            ):
                my_stay_group = True
            assign.my_stay_group = my_stay_group

    def _search_my_stay_group(self, operator, value):
        return self.env["stay.stay"]._search_my_stay_group(operator, value)

    @api.constrains("room_id", "guest_qty", "arrival_datetime", "departure_datetime")
    def _check_room_assign(self):
        for assign in self:
            if assign.guest_qty > assign.room_id.bed_qty:
                raise UserError(
                    _("Room %s only has %d bed capacity, not %d!")
                    % (
                        assign.room_id.display_name,
                        assign.room_id.bed_qty,
                        assign.guest_qty,
                    )
                )
            if assign.room_id:
                if assign.room_id.bed_qty > 1 and assign.room_id.allow_simultaneous:
                    assign._check_reservation_conflict_multi()
                else:
                    assign._check_reservation_conflict_single()

    def _check_reservation_conflict_single(self):
        self.ensure_one()
        assert self.room_id
        conflict_domain = self.stay_id._get_assign_base_conflict_domain()
        conflict_domain += [("id", "!=", self.id), ("room_id", "=", self.room_id.id)]
        conflict_assign = self.search(conflict_domain, limit=1)
        if conflict_assign:
            conflict_stay = conflict_assign.stay_id
            raise ValidationError(
                _(
                    "This stay conflicts with stay %s of '%s' "
                    "from %s %s to %s %s in room %s."
                )
                % (
                    conflict_stay.name,
                    conflict_stay.partner_name,
                    format_date(self.env, conflict_stay.arrival_date),
                    conflict_stay._fields["arrival_time"].convert_to_export(
                        conflict_stay.arrival_time, conflict_stay
                    ),
                    format_date(self.env, conflict_stay.departure_date),
                    conflict_stay._fields["departure_time"].convert_to_export(
                        conflict_stay.departure_time, conflict_stay
                    ),
                    conflict_assign.room_id.display_name,
                )
            )

    def _check_reservation_conflict_multi(self):
        self.ensure_one()
        assert self.room_id
        guest_qty = self.guest_qty
        bed_qty = self.room_id.bed_qty
        assert bed_qty > 1
        assert guest_qty <= bed_qty
        assert self.arrival_date < self.departure_date
        date = self.arrival_date
        departure_date = self.departure_date
        while date < departure_date:
            rg_res = self.read_group(
                [
                    ("room_id", "=", self.room_id.id),
                    ("arrival_date", "<=", date),
                    ("departure_date", ">", date),
                ],
                ["guest_qty"],
                [],
            )
            # The result includes the current stay
            qty = rg_res and rg_res[0]["guest_qty"] or 0
            if qty > bed_qty:
                raise ValidationError(
                    _(
                        "Conflict in room %s: with stay '%s', we would have a total of "
                        "%d guests on %s whereas that room only has %d beds."
                    )
                    % (
                        self.room_id.display_name,
                        self.stay_id.name,
                        qty,
                        format_date(self.env, date),
                        bed_qty,
                    )
                )
            date += relativedelta(days=1)

    @api.depends(
        "stay_id",
        "stay_group_id",
        "room_id",
        "company_id",
        "arrival_datetime",
        "departure_datetime",
    )
    def _compute_conflict_room_ids(self):
        # Current implementation:
        # we exlude ONLY single rooms and
        # multi-bed-rooms with allow_simultaneous = False
        # that are already occupied (we call them "potential_excl_rooms")
        # For that, we must search on conflicting assignments linked to
        # those rooms only
        sro = self.env["stay.room"]
        company_id2potential_excl_room_ids = defaultdict(list)
        room_sr = sro.search_read([("allow_simultaneous", "=", False)], ["company_id"])
        for room in room_sr:
            company_id = room["company_id"][0]
            company_id2potential_excl_room_ids[company_id].append(room["id"])

        for assign in self:
            company_id = assign.company_id.id or self.env.company.id
            potential_excl_room_ids = company_id2potential_excl_room_ids.get(
                company_id, []
            )
            conflict_domain = assign.stay_id._get_assign_base_conflict_domain()
            conflict_domain.append(("room_id", "in", potential_excl_room_ids))
            if assign._origin.id:
                conflict_domain.append(("id", "!=", assign._origin.id))
            # One potential cause of problem: if the user deletes an assign line
            # and creates a new one (without save in between), Odoo will not
            # propose the room of the deleted assign line (until a new "save")
            # because the deleted assign line still exists in DB
            conflict_assigns = self.search_read(conflict_domain, ["room_id"])
            conflict_room_ids = {cass["room_id"][0] for cass in conflict_assigns}
            assign.conflict_room_ids = list(conflict_room_ids)

    @api.depends("partner_name", "arrival_time", "departure_time", "room_id")
    def name_get(self):
        res = []
        with_room = self._context.get("display_name_with_room")
        for assign in self:
            name = assign.partner_name
            if assign.guest_qty > 1:
                name = f"({assign.guest_qty}) {name}"
            if with_room:
                name = f"{name} {assign.room_id.code or assign.room_id.name}"
            res.append((assign.id, name))
        return res

    @api.onchange("room_id")
    def room_id_change(self):
        if (
            self.stay_id
            and self.room_id
            and self.room_id.bed_qty
            and not self.guest_qty
        ):
            if self.stay_id.guest_qty_to_assign:
                if self.stay_id.guest_qty_to_assign <= self.room_id.bed_qty:
                    self.guest_qty = self.stay_id.guest_qty_to_assign
                else:
                    self.guest_qty = self.room_id.bed_qty

    def show_stay(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stay.stay_action")
        action.update(
            {
                "view_mode": "form,tree,calendar,graph,pivot",
                "res_id": self.stay_id.id,
                "views": False,
            }
        )
        return action

    def _report_fire_mobiles(self):
        self.ensure_one()
        res = set()
        if self.stay_id.partner_id:
            if "res.partner.phone" in self.env:
                partner_phones = self.env["res.partner.phone"].search(
                    [
                        ("partner_id", "=", self.stay_id.partner_id.id),
                        ("type", "in", ("5_mobile_primary", "6_mobile_secondary")),
                        ("phone", "!=", False),
                    ]
                )
                for partner_phone in partner_phones:
                    mobile_str = partner_phone.phone
                    if partner_phone.note:
                        mobile_str = f"{mobile_str} ({partner_phone.note})"
                    res.add(mobile_str)
            else:
                if self.stay_id.partner_id.mobile:
                    res.add(self.stay_id.partner_id.mobile)
        return res


class StayRefectory(models.Model):
    _name = "stay.refectory"
    _description = "Refectory"
    _order = "sequence, id"
    _rec_name = "display_name"

    sequence = fields.Integer(default=10)
    code = fields.Char(string="Code")
    name = fields.Char(string="Name", required=True)
    capacity = fields.Integer(string="Capacity")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        ondelete="cascade",
        required=True,
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        (
            "company_code_uniq",
            "unique(company_id, code)",
            "A refectory with this code already exists in this company.",
        )
    ]

    @api.depends("name", "code")
    def name_get(self):
        res = []
        for ref in self:
            name = ref.name
            if ref.code:
                name = "[%s] %s" % (ref.code, name)
            res.append((ref.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        if name and operator == "ilike":
            recs = self.search([("code", "=", name)] + args, limit=limit)
            if recs:
                return recs.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)


class StayRoom(models.Model):
    _name = "stay.room"
    _description = "Room"
    _order = "sequence, id"
    _check_company_auto = True

    code = fields.Char(string="Code", copy=False)
    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        ondelete="cascade",
        required=True,
        default=lambda self: self.env.company,
    )
    sequence = fields.Integer(default=10)
    group_id = fields.Many2one(
        "stay.group",
        string="Group",
        check_company=True,
        domain="[('company_id', '=', company_id)]",
        index=True,
    )
    building_id = fields.Many2one("stay.building", index=True, ondelete="restrict")
    bed_qty = fields.Integer(string="Number of beds", default=1)
    allow_simultaneous = fields.Boolean(
        string="Allow simultaneous",
        help="This option applies for rooms where bed quantity > 1. You "
        "should enable this option if you allow to have several stays "
        "at the same time in the room.",
    )
    active = fields.Boolean(default=True)
    notes = fields.Text()
    to_clean = fields.Char(
        string="To Clean",
        help="When the field has a value, it means the room must be cleaned "
        "(when a stay is terminated, this field is auto-set with the "
        "stay description). When the room is cleaned, the field is emptied.",
    )
    # for filter
    my_stay_group = fields.Boolean(
        compute="_compute_my_stay_group", search="_search_my_stay_group"
    )
    fire_report_exclude = fields.Boolean(string="Exclude from Fire Report")
    fire_report_sequence = fields.Integer(string="Order for Fire Report")

    _sql_constraints = [
        (
            "company_code_uniq",
            "unique(company_id, code)",
            "A room with this code already exists in this company.",
        ),
        (
            "bed_qty_positive",
            "CHECK(bed_qty > 0)",
            "The number of beds must be positive.",
        ),
    ]

    @api.depends_context("uid")
    @api.depends("group_id")
    def _compute_my_stay_group(self):
        for room in self:
            my_stay_group = False
            if (
                self.env.user.context_stay_group_id
                and room.group_id == self.env.user.context_stay_group_id
            ):
                my_stay_group = True
            room.my_stay_group = my_stay_group

    def _search_my_stay_group(self, operator, value):
        return self.env["stay.stay"]._search_my_stay_group(operator, value)

    @api.constrains("allow_simultaneous", "bed_qty")
    def _check_room_config(self):
        for room in self:
            if room.allow_simultaneous and room.bed_qty <= 1:
                raise ValidationError(
                    _(
                        "Room %s has the option Allow simultaneous, but this option "
                        "is only for rooms with several beds."
                    )
                    % room.display_name
                )

    @api.onchange("allow_simultaneous", "bed_qty")
    def room_config_change(self):
        if self.allow_simultaneous and self.bed_qty <= 1:
            self.allow_simultaneous = False

    @api.depends("name", "code")
    def name_get(self):
        res = []
        for room in self:
            name = room.name
            if room.code:
                name = "[%s] %s" % (room.code, name)
            res.append((room.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        if name and operator == "ilike":
            recs = self.search([("code", "=", name)] + args, limit=limit)
            if recs:
                return recs.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    def mark_as_cleaned(self):
        self.write({"to_clean": False})

    def action_archive(self):
        today = fields.Date.context_today(self)
        assign = self.env["stay.room.assign"].search(
            [
                ("room_id", "in", self.ids),
                ("departure_date", ">=", today),
            ],
            limit=1,
        )
        if assign:
            raise UserError(
                _(
                    "The room '%(room)s' cannot be archived because the stay %(stay)s "
                    "which ends on %(departure_date)s uses that room.",
                    room=assign.room_id.display_name,
                    stay=assign.stay_id.name,
                    departure_date=format_date(self.env, assign.stay_id.departure_date),
                )
            )
        return super().action_archive()


class StayGroup(models.Model):
    _name = "stay.group"
    _description = "Stay Group"
    _order = "sequence, id"
    _check_company_auto = True

    name = fields.Char(string="Group Name", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        ondelete="cascade",
        required=True,
        default=lambda self: self.env.company,
    )
    sequence = fields.Integer()
    room_ids = fields.One2many("stay.room", "group_id", string="Rooms")
    notify_user_ids = fields.Many2many("res.users", string="Users Notified by E-mail")
    default_refectory_id = fields.Many2one(
        "stay.refectory",
        string="Default Refectory",
        ondelete="restrict",
        check_company=True,
    )
    default_no_meals = fields.Boolean(string="No Meals by Default")

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique(name, company_id)",
            "A group with this name already exists in this company.",
        )
    ]

    @api.model
    def _stay_notify(self):
        logger.info("Start stay arrival notify cron")
        today = fields.Date.context_today(self)
        sso = self.env["stay.stay"]
        fields_get_time = dict(
            sso.fields_get("arrival_time", "selection")["arrival_time"]["selection"]
        )
        for company in self.env["res.company"].search([]):
            groups = self.search(
                [("notify_user_ids", "!=", False), ("company_id", "=", company.id)]
            )
            group2email_to_list = {}
            for group in groups:
                email_to_list = ", ".join(
                    [u.email for u in group.notify_user_ids if u.email]
                )
                if email_to_list:
                    group2email_to_list[group] = email_to_list
            # Add stays without group
            if company.stay_notify_user_ids:
                email_to_list = ", ".join(
                    [u.email for u in company.stay_notify_user_ids if u.email]
                )
                if email_to_list:
                    group2email_to_list[False] = email_to_list
            for group, email_to_list in group2email_to_list.items():
                group_id = group and group.id or False
                stays = sso.search(
                    [
                        ("arrival_date", "=", today),
                        ("group_id", "=", group_id),
                    ],
                    order="partner_name",
                )
                if stays:
                    stay_list = []
                    for stay in stays:
                        stay_list.append(
                            {
                                "partner_name": stay.partner_name,
                                "guest_qty": stay.guest_qty,
                                "arrival_time": fields_get_time[stay.arrival_time],
                                "arrival_note": stay.arrival_note or "",
                                "rooms": stay.rooms_display_name,
                                "departure_date": stay.departure_date,
                                "departure_time": fields_get_time[stay.departure_time],
                                "departure_note": stay.departure_note or "",
                                "notes": stay.notes or "",
                            }
                        )
                    self.env.ref("stay.stay_notify").with_context(
                        stay_list=stay_list,
                        date=today,
                        email_to_list=email_to_list,
                        email_from=company.email or self.env.user.email,
                        group_name=group and group.name or False,
                    ).send_mail(company.id)
                    logger.info(
                        "Stay notification mail sent to %s for group ID %s",
                        email_to_list,
                        group_id,
                    )
                else:
                    logger.info("No arrivals on %s for group ID %s", today, group_id)
        logger.info("End stay arrival notify cron")


class StayLine(models.Model):
    _name = "stay.line"
    _description = "Stay Journal"
    _rec_name = "partner_name"
    _order = "date"
    _check_company_auto = True

    stay_id = fields.Many2one(
        "stay.stay", string="Stay", check_company=True, ondelete="cascade"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    date = fields.Date(
        string="Date", required=True, default=fields.Date.context_today, index=True
    )
    breakfast_qty = fields.Integer(string="Breakfast")
    lunch_qty = fields.Integer(string="Lunches")
    dinner_qty = fields.Integer(string="Dinners")
    bed_night_qty = fields.Integer(string="Bed Nights")
    partner_id = fields.Many2one(
        "res.partner",
        string="Guest",
        help="If guest is anonymous, leave this field empty.",
    )
    partner_name = fields.Text(
        "Guest Names",
        required=True,
        compute="_compute_partner_name",
        store=True,
        readonly=False,
    )
    refectory_id = fields.Many2one(
        "stay.refectory",
        string="Refectory",
        check_company=True,
        default=lambda self: self.env.company.default_refectory_id,
    )
    rooms_display_name = fields.Char(related="stay_id.rooms_display_name", store=True)
    group_id = fields.Many2one(
        "stay.group", compute="_compute_group_id", store=True, readonly=False
    )
    # for filter
    my_stay_group = fields.Boolean(
        compute="_compute_my_stay_group", search="_search_my_stay_group"
    )

    @api.depends("stay_id.partner_name", "partner_id")
    def _compute_partner_name(self):
        for line in self:
            partner_name = False
            if line.stay_id:
                partner_name = line.stay_id.partner_name
            elif line.partner_id:
                partner_name = line.partner_id._stay_get_partner_name()
            line.partner_name = partner_name

    @api.depends("stay_id")
    def _compute_group_id(self):
        for line in self:
            group_id = False
            if line.stay_id:
                group_id = line.stay_id.group_id.id or False
            else:
                group_id = self.env.user.context_stay_group_id.id or False
            line.group_id = group_id

    @api.depends_context("uid")
    @api.depends("group_id")
    def _compute_my_stay_group(self):
        for line in self:
            my_stay_group = False
            if (
                self.env.user.context_stay_group_id
                and line.group_id == self.env.user.context_stay_group_id
            ):
                my_stay_group = True
            line.my_stay_group = my_stay_group

    def _search_my_stay_group(self, operator, value):
        return self.env["stay.stay"]._search_my_stay_group(operator, value)

    @api.constrains("refectory_id", "breakfast_qty", "lunch_qty", "dinner_qty")
    def _check_room_refectory(self):
        for line in self:
            if (
                line.lunch_qty or line.dinner_qty or line.breakfast_qty
            ) and not line.refectory_id:
                raise ValidationError(
                    _("Missing refectory for guest '%s' on %s.")
                    % (line.partner_name, format_date(self.env, line.date))
                )

    _sql_constraints = [
        (
            "lunch_qty_positive",
            "CHECK (lunch_qty >= 0)",
            "The number of lunches must be positive or null.",
        ),
        (
            "dinner_qty_positive",
            "CHECK (dinner_qty >= 0)",
            "The number of dinners must be positive or null.",
        ),
        (
            "bed_night_qty_positive",
            "CHECK (bed_night_qty >= 0)",
            "The number of bed nights must be positive or null.",
        ),
    ]


class StayDateLabel(models.Model):
    _name = "stay.date.label"
    _description = "Stay Date Label"
    _order = "date desc"

    date = fields.Date(required=True, index=True)
    name = fields.Char(string="Label")

    _sql_constraints = [("date_uniq", "unique(date)", "This date already exists.")]

    @api.model
    def _get_date_label(self, date):
        res = False
        if date:
            date_label = self.env["stay.date.label"].search(
                [("date", "=", date)], limit=1
            )
            res = date_label and date_label.name or False
        return res
