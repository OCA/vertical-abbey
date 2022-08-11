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

TIMEDICT = {
    "morning": "09:00",
    "afternoon": "15:00",
    "evening": "20:00",
    "unknown": "08:00",
}
TIME2CODE = {
    "morning": _("Mo"),
    "afternoon": _("Af"),
    "evening": _("Ev"),
}


class StayStay(models.Model):
    _name = "stay.stay"
    _description = "Guest Stay"
    _order = "arrival_date desc"
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
    partner_name = fields.Text("Guest Names", required=True, tracking=True)
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
        states={"draft": [("readonly", True)], "cancel": [("readonly", True)]},
        copy=True,
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
    )
    # to workaround the bug https://github.com/OCA/web/issues/1446
    # in v12+, if this PR is merged https://github.com/OCA/web/issues/1446
    # the we could use color_field
    user_id = fields.Many2one(related="group_id.user_id", store=True)
    line_ids = fields.One2many(
        "stay.line",
        "stay_id",
        string="Stay Lines",
        states={"draft": [("readonly", True)], "cancel": [("readonly", True)]},
    )
    refectory_id = fields.Many2one(
        "stay.refectory",
        string="Refectory",
        check_company=True,
        default=lambda self: self.env.company.default_refectory_id,
    )
    no_meals = fields.Boolean(
        string="No Meals",
        tracking=True,
        help="The stay lines generated from this stay will not have "
        "lunchs nor dinners by default.",
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
                guest_qty_to_assign -= assign.guest_qty
                room_codes.append(assign.room_id.code or assign.room_id.name)
            if room_codes:
                rooms_display_name = "-".join(room_codes)
            else:
                rooms_display_name = "\u2205"

            if stay.state in ("draft", "cancel"):
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
        if date_aware_local.hour < 12:
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
            if (
                stay.arrival_date
                and stay.arrival_time
                and stay.arrival_time != "unknown"
            ):
                datetime_naive_utc = self._convert_to_datetime_naive_utc(
                    stay.arrival_date, stay.arrival_time
                )
            stay.arrival_datetime = datetime_naive_utc

    @api.depends("departure_date", "departure_time")
    def _compute_departure_datetime(self):
        for stay in self:
            datetime_naive_utc = False
            if (
                stay.departure_date
                and stay.departure_time
                and stay.departure_time != "unknown"
            ):
                datetime_naive_utc = self._convert_to_datetime_naive_utc(
                    stay.departure_date, stay.departure_time
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
                        "Arrival time cannot be set to unknown"
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

    @api.onchange("partner_id")
    def partner_id_change(self):
        if self.partner_id:
            partner = self.partner_id
            partner_name = partner.name
            if partner.title and not partner.is_company:
                partner_lg = partner
                if partner.lang:
                    partner_lg = partner.with_context(lang=partner.lang)
                title = partner_lg.title.shortcut or partner_lg.title.name
                partner_name = "%s %s" % (title, partner_name)
            self.partner_name = partner_name

    @api.onchange("group_id")
    def group_id_change(self):
        if self.group_id and self.group_id.default_refectory_id:
            self.refectory_id = self.group_id.default_refectory_id

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
                    "refectory_id": False,
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
        domain="[('id', 'in', room_domain_ids)]",
    )
    room_domain_ids = fields.Many2many(
        "stay.room", compute="_compute_room_domain_ids", string="Available Rooms"
    )
    guest_qty = fields.Integer(string="Guest Quantity", required=True)
    # Related fields
    group_id = fields.Many2one(related="room_id.group_id", store=True)
    stay_group_id = fields.Many2one(
        related="stay_id.group_id", store=True, string="Stay Group"
    )
    # The field group_id_integer is used for colors in timeline view
    group_id_integer = fields.Integer(related="room_id.group_id.id", string="Group ID")
    user_id = fields.Many2one(related="room_id.group_id.user_id", store=True)
    arrival_date = fields.Date(related="stay_id.arrival_date", store=True)
    arrival_time = fields.Selection(related="stay_id.arrival_time", store=True)
    arrival_datetime = fields.Datetime(related="stay_id.arrival_datetime", store=True)
    departure_date = fields.Date(related="stay_id.departure_date", store=True)
    departure_time = fields.Selection(related="stay_id.departure_time", store=True)
    departure_datetime = fields.Datetime(
        related="stay_id.departure_datetime", store=True
    )
    partner_id = fields.Many2one(related="stay_id.partner_id", store=True)
    partner_name = fields.Text(related="stay_id.partner_name", store=True)
    company_id = fields.Many2one(related="stay_id.company_id", store=True)

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
        # No conflict IF :
        # leaves before my arrival (or same day)
        # OR arrivers after my departure (or same day)
        # CONTRARY :
        # leaves after my arrival
        # AND arrives before my departure
        conflict_assign = self.search(
            [
                ("id", "!=", self.id),
                ("room_id", "=", self.room_id.id),
                ("departure_datetime", ">=", self.arrival_datetime),
                ("arrival_datetime", "<=", self.departure_datetime),
            ],
            limit=1,
        )
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
    def _compute_room_domain_ids(self):
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

            conflict_domain = [
                ("room_id", "in", potential_excl_room_ids),
                ("departure_datetime", ">=", assign.arrival_datetime),
                ("arrival_datetime", "<=", assign.departure_datetime),
            ]
            if assign._origin.id:
                conflict_domain.append(("id", "!=", assign._origin.id))
            conflict_assigns = self.search_read(conflict_domain, ["room_id"])
            conflict_rooms = {x["room_id"][0]: True for x in conflict_assigns}

            eligible_domain = [
                ("company_id", "=", company_id),
                ("id", "not in", list(conflict_rooms.keys())),
            ]
            if assign.stay_group_id:
                eligible_domain += [
                    ("group_id", "in", (False, assign.stay_group_id.id))
                ]
            eligible_rooms = sro.search(eligible_domain)
            assign.room_domain_ids = eligible_rooms.ids

    @api.depends("partner_name", "arrival_time", "departure_time", "room_id")
    def name_get(self):
        res = []
        for assign in self:
            name = "[%s] %s, %s, %d [%s]" % (
                TIME2CODE[assign.arrival_time],
                shorten(assign.partner_name, 20, placeholder="..."),
                assign.room_id.code or assign.room_id.name,
                assign.guest_qty,
                TIME2CODE[assign.departure_time],
            )
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


class StayRefectory(models.Model):
    _name = "stay.refectory"
    _description = "Refectory"
    _order = "sequence, id"
    _rec_name = "display_name"

    sequence = fields.Integer(default=10)
    code = fields.Char(string="Code", size=10)
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

    code = fields.Char(string="Code", size=10, copy=False)
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
    )
    user_id = fields.Many2one(related="group_id.user_id", store=True, readonly=True)
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
    user_id = fields.Many2one("res.users", string="In Charge")
    sequence = fields.Integer()
    room_ids = fields.One2many("stay.room", "group_id", string="Rooms")
    notify_user_ids = fields.Many2many("res.users", string="Users Notified by E-mail")
    default_refectory_id = fields.Many2one(
        "stay.refectory",
        string="Default Refectory",
        ondelete="restrict",
        check_company=True,
    )

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
        for group in self.search([("notify_user_ids", "!=", False)]):
            stays = sso.search(
                [
                    ("arrival_date", "=", today),
                    ("group_id", "=", group.id),
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
                            "rooms": stay.rooms_display_name,
                            "departure_date": stay.departure_date,
                            "departure_time": fields_get_time[stay.departure_time],
                        }
                    )
                email_to_list = ",".join(
                    [u.email for u in group.notify_user_ids if u.email]
                )
                email_from = (
                    self.company_id and self.company_id.email or self.env.user.email
                )
                self.env.ref("stay.stay_notify").with_context(
                    stay_list=stay_list,
                    date=today,
                    email_to_list=email_to_list,
                    email_from=email_from,
                ).send_mail(group.id)
                logger.info(
                    "Stay notification mail sent for group %s", group.display_name
                )
            else:
                logger.info("No arrivals on %s for group %s", today, group.display_name)
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
    partner_name = fields.Text("Guest Names", required=True)
    refectory_id = fields.Many2one(
        "stay.refectory",
        string="Refectory",
        check_company=True,
        default=lambda self: self.env.company.default_refectory_id,
    )
    rooms_display_name = fields.Char(related="stay_id.rooms_display_name", store=True)
    group_id = fields.Many2one(related="stay_id.group_id", store=True)
    user_id = fields.Many2one(related="stay_id.group_id.user_id", store=True)

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

    @api.onchange("partner_id")
    def partner_id_change(self):
        if self.partner_id:
            partner = self.partner_id
            partner_name = partner.name
            if partner.title and not partner.is_company:
                partner_lg = partner
                if partner.lang:
                    partner_lg = partner.with_context(lang=partner.lang)
                title = partner_lg.title.shortcut or partner_lg.title.name
                partner_name = "%s %s" % (title, partner_name)
            self.partner_name = partner_name


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
