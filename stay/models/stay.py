# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# @author: Brother Irénée
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date

logger = logging.getLogger(__name__)

TIMEDICT = {
    "morning": "09:00",
    "afternoon": "15:00",
    "evening": "20:00",
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
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Guest",
        ondelete="restrict",
        help="If guest is anonymous, leave this field empty.",
    )
    partner_name = fields.Text("Guest Name", required=True, tracking=True)
    guest_qty = fields.Integer(string="Guest Quantity", default=1, tracking=True)
    arrival_date = fields.Date(
        string="Arrival Date", required=True, tracking=True, index=True
    )
    arrival_time = fields.Selection(
        [
            ("morning", "Morning"),
            ("afternoon", "Afternoon"),
            ("evening", "Evening"),
        ],
        string="Arrival Time",
        required=True,
        tracking=True,
    )
    arrival_datetime = fields.Datetime(
        compute="_compute_arrival_datetime", store=True, string="Arrival Date and Time"
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
        ],
        string="Departure Time",
        required=True,
        tracking=True,
    )
    departure_datetime = fields.Datetime(
        compute="_compute_departure_datetime",
        store=True,
        string="Departure Date and Time",
    )
    departure_note = fields.Char(string="Departure Note")
    room_id = fields.Many2one(
        "stay.room",
        string="Room",
        tracking=True,
        copy=False,
        domain="[('company_id', '=', company_id)]",
        ondelete="restrict",
        index=True,
        check_company=True,
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
    group_id_integer = fields.Integer(related="group_id.id", string="Group ID")
    # The field group_id_integer is used for colors in timeline view
    # to workaround the bug https://github.com/OCA/web/issues/1446
    # in v12+, if this PR is merged https://github.com/OCA/web/issues/1446
    # the we could use color_field
    user_id = fields.Many2one(related="group_id.user_id", store=True)
    line_ids = fields.One2many("stay.line", "stay_id", string="Stay Lines")
    no_meals = fields.Boolean(
        string="No Meals",
        help="The stay lines generated from this stay will not have "
        "lunchs nor dinners by default.",
    )
    calendar_display_name = fields.Char(
        compute="_compute_calendar_display_name", store=False
    )
    # don't store because contains translation

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

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("stay.stay")
        return super().create(vals)

    @api.model
    def _convert_to_datetime_naive_utc(self, date_str, time_sel):
        # Convert from local time to datetime naive UTC
        datetime_str = "%s %s" % (date_str, TIMEDICT[time_sel])
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

    @api.depends("arrival_date", "arrival_time")
    def _compute_arrival_datetime(self):
        for stay in self:
            datetime_naive_utc = False
            if stay.arrival_date and stay.arrival_time:
                datetime_naive_utc = self._convert_to_datetime_naive_utc(
                    stay.arrival_date, stay.arrival_time
                )
            stay.arrival_datetime = datetime_naive_utc

    @api.depends("departure_date", "departure_time")
    def _compute_departure_datetime(self):
        for stay in self:
            datetime_naive_utc = False
            if stay.departure_date and stay.departure_time:
                datetime_naive_utc = self._convert_to_datetime_naive_utc(
                    stay.departure_date, stay.departure_time
                )
            stay.departure_datetime = datetime_naive_utc

    @api.depends("partner_name", "arrival_time", "departure_time", "room_id")
    def _compute_calendar_display_name(self):
        for stay in self:
            if stay.room_id:
                room = stay.room_id.code or stay.room_id.name
            else:
                room = _("No Room")
            stay.calendar_display_name = "[%s] %s, %s, %d [%s]" % (
                TIME2CODE[stay.arrival_time],
                stay.partner_name,
                room,
                stay.guest_qty,
                TIME2CODE[stay.departure_time],
            )

    @api.constrains(
        "departure_date",
        "departure_time",
        "arrival_date",
        "arrival_time",
        "room_id",
        "group_id",
        "guest_qty",
    )
    def _check_stay(self):
        for stay in self:
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
            if stay.room_id:
                if stay.room_id.group_id and stay.group_id != stay.room_id.group_id:
                    raise ValidationError(
                        _(
                            "For stay '%s', the room '%s' is linked to "
                            "group '%s', but the selected group is '%s'."
                        )
                        % (
                            stay.display_name,
                            stay.room_id.display_name,
                            stay.room_id.group_id.display_name,
                            stay.group_id.display_name,
                        )
                    )
                if stay.guest_qty > stay.room_id.bed_qty:
                    raise ValidationError(
                        _(
                            "Stay '%s' has %d guest(s), but the selected room "
                            "'%s' only has %d bed(s)."
                        )
                        % (
                            stay.display_name,
                            stay.guest_qty,
                            stay.room_id.display_name,
                            stay.room_id.bed_qty,
                        )
                    )
                if self.room_id.bed_qty > 1 and self.room_id.allow_simultaneous:
                    stay._check_reservation_conflict_multi()
                else:
                    stay._check_reservation_conflict_single()

    def _check_reservation_conflict_single(self):
        self.ensure_one()
        assert self.room_id
        # No conflict IF :
        # leaves before my arrival (or same day)
        # OR arrivers after my departure (or same day)
        # CONTRARY :
        # leaves after my arrival
        # AND arrives before my departure
        conflict_stay = self.search(
            [
                ("id", "!=", self.id),
                ("room_id", "=", self.room_id.id),
                ("departure_datetime", ">=", self.arrival_datetime),
                ("arrival_datetime", "<=", self.departure_datetime),
            ],
            limit=1,
        )
        if conflict_stay:
            raise ValidationError(
                _(
                    "This stay conflicts with stay %s of '%s' "
                    "from %s %s to %s %s in room %s."
                )
                % (
                    conflict_stay.name,
                    conflict_stay.partner_name,
                    format_date(self.env, conflict_stay.arrival_date),
                    conflict_stay.arrival_time,
                    format_date(self.env, conflict_stay.departure_date),
                    conflict_stay.departure_time,
                    conflict_stay.room_id.display_name,
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
                        "With stay '%s' (%d guests), we would have a total of "
                        "%d guest on %s whereas room '%s' only has %d beds."
                    )
                    % (
                        self.display_name,
                        guest_qty,
                        qty,
                        format_date(self.env, date),
                        self.room_id.display_name,
                        bed_qty,
                    )
                )
            date += relativedelta(days=1)

    @api.depends("partner_name", "name", "room_id")
    def name_get(self):
        res = []
        for stay in self:
            if self._context.get("stay_name_get_partner_name"):
                name = stay.partner_name
            elif self._context.get("stay_name_get_partner_name_qty"):
                name = stay.partner_name
                if stay.guest_qty > 1:
                    name += " (%d)" % stay.guest_qty
            elif self._context.get("stay_name_get_partner_name_qty_room"):
                name = stay.partner_name
                if stay.guest_qty > 1:
                    name += " (%d)" % stay.guest_qty
                if stay.room_id:
                    name += " [%s]" % stay.room_id.code or stay.room_id.name
            else:
                name = stay.name
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

    @api.onchange("room_id")
    def room_id_change(self):
        if self.room_id:
            self.no_meals = self.room_id.no_meals
            if self.room_id.group_id:
                self.group_id = self.room_id.group_id.id

    @api.onchange("group_id")
    def group_id_change(self):
        res = {"domain": {"room_id": []}}
        if self.group_id and not self.room_id:
            res["domain"]["room_id"] = [("group_id", "=", self.group_id.id)]
        return res


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
    _rec_name = "display_name"
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
    no_meals = fields.Boolean(
        string="No Meals",
        help="If active, the stays linked to this room will have the "
        "same option active by default.",
    )
    notes = fields.Text()

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


class StayGroup(models.Model):
    _name = "stay.group"
    _description = "Stay Group"
    _order = "sequence, id"

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
                            "room": stay.room_id and stay.room_id.display_name or "",
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
    _order = "date desc"
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
    room_id = fields.Many2one(
        "stay.room",
        string="Room",
        ondelete="restrict",
        domain="[('company_id', '=', company_id)]",
        index=True,
        check_company=True,
    )
    group_id = fields.Many2one(related="room_id.group_id", store=True)
    user_id = fields.Many2one(related="room_id.group_id.user_id", store=True)

    @api.constrains("refectory_id", "lunch_qty", "dinner_qty", "date", "room_id")
    def _check_room_refectory(self):
        for line in self:
            if (line.lunch_qty or line.dinner_qty) and not line.refectory_id:
                raise ValidationError(
                    _("Missing refectory for guest '%s' on %s.")
                    % (line.partner_name, format_date(self.env, line.date))
                )
            if line.room_id and line.bed_night_qty:
                same_room_same_day_line = self.search(
                    [
                        ("date", "=", line.date),
                        ("room_id", "=", line.room_id.id),
                        ("bed_night_qty", ">", 0),
                    ]
                )
                guests_in_room_qty = 0
                for same_room in same_room_same_day_line:
                    guests_in_room_qty += same_room.bed_night_qty
                if guests_in_room_qty > line.room_id.bed_qty:
                    raise ValidationError(
                        _(
                            "The room '%s' is booked or all beds of the "
                            "room are booked."
                        )
                        % line.room_id.display_name
                    )

    _sql_constraints = [
        (
            "lunch_qty_positive",
            "CHECK (lunch_qty >= 0)",
            "The number of lunches must be positive or null",
        ),
        (
            "dinner_qty_positive",
            "CHECK (dinner_qty >= 0)",
            "The number of dinners must be positive or null",
        ),
        (
            "bed_night_qty_positive",
            "CHECK (bed_night_qty >= 0)",
            "The number of bed nights must be positive or null",
        ),
    ]

    @api.onchange("partner_id")
    def _partner_id_change(self):
        if self.partner_id:
            self.partner_name = self.partner_id.display_name


class StayDateLabel(models.Model):
    _name = "stay.date.label"
    _description = "Stay Date Label"
    _order = "date desc"

    date = fields.Date(required=True, index=True)
    name = fields.Char(string="Label")

    _sql_constraints = [("date_uniq", "unique(date)", "This date already exists.")]
