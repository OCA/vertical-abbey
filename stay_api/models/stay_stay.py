# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from odoo import _, api, fields, models

logger = logging.getLogger(__name__)


UUID_VERSION = 4


class StayStay(models.Model):
    _inherit = "stay.stay"

    controller_mode = fields.Selection(
        [
            ("created", "Created"),
            ("updated", "Updated"),
        ],
        readonly=True,
        string="Web Form Mode",
    )
    controller_firstname = fields.Char(tracking=True, string="Firstname")
    controller_lastname = fields.Char(tracking=True, string="Lastname")
    controller_title = fields.Selection(
        [
            ("mister", "Mister"),
            ("madam", "Madam"),
            ("miss", "Miss"),
        ],
        tracking=True,
        string="Title",
    )
    controller_email = fields.Char(tracking=True, string="E-mail")
    controller_phone = fields.Char(tracking=True, string="Phone")
    controller_mobile = fields.Char(tracking=True, string="Mobile")
    controller_message = fields.Char(string="Guest Message")
    controller_notes = fields.Text(string="Web Form Other Information")
    controller_street = fields.Char(string="Address Line 1")
    controller_street2 = fields.Char(string="Address Line 2")
    controller_zip = fields.Char(string="ZIP")
    controller_city = fields.Char(string="City")
    controller_country_id = fields.Many2one("res.country", string="Country")
    controller_uuid = fields.Char(string="UUID", readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["controller_uuid"] = str(uuid4())
        return super().create(vals_list)

    @api.model
    def _get_stay_from_uuid(
        self, uuid, api_name, ignore_states=None, raise_states=None
    ):
        assert uuid
        assert api_name
        try:
            UUID(uuid, version=UUID_VERSION)
        except ValueError:
            error_msg = f"uuid '{uuid}' is not a valid uuid version 4."
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
            )
        stays = self.search([("controller_uuid", "=", uuid)], order="id desc")
        if not stays:
            error_msg = f"No stay with uuid '{uuid}' in the database."
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
            )
        if len(stays) > 1:
            logger.warning(
                "There are %d stays with UUID=%s that should almost never happen!",
                len(stays),
                uuid,
            )
        stay = stays[0]
        state2label = dict(self.fields_get("state", "selection")["state"]["selection"])
        if ignore_states and stay.state in ignore_states:
            logger.warning(
                "API %s: stay %s ID %d is in state %s, ignoring.",
                api_name,
                stay.name,
                stay.id,
                stay.state,
            )
            stay.message_post(
                body=_(
                    "API call %(api_name)s ignored because the stay "
                    "is in %(state_label)s state.",
                    api_name=api_name,
                    state_label=state2label[stay.state],
                )
            )
            return False
        if raise_states and stay.state in raise_states:
            logger.warning(
                "API %s: stay %s ID %d is in state %s, raising error.",
                api_name,
                stay.name,
                stay.id,
                stay.state,
            )
            stay.message_post(
                body=_(
                    "API call %(api_name)s returned an error because "
                    "the stay is in %(state_label)s state.",
                    api_name=api_name,
                    state_label=state2label[stay.state],
                )
            )
            error_msg = f"Request blocked because stay is in {stay.state} state."
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
            )
        logger.info(
            "API %s: stay %s ID %d is in state %s, processing.",
            api_name,
            stay.name,
            stay.id,
            stay.state,
        )
        stay.message_post(
            body=_(
                "API call %(api_name)s accepted because stay is in %(state_label)s state.",
                api_name=api_name,
                state_label=state2label[stay.state],
            )
        )
        return stay

    @api.model
    def _controller_prepare_create_update(self, cobject, try_match_partner=True):
        assert cobject
        to_strip_fields = [
            "firstname",
            "lastname",
            "street",
            "street2",
            "zip",
            "city",
            "country_code",
            "email",
            "phone",
            "mobile",
            "departure_note",
            "arrival_note",
        ]
        for to_strip_field in to_strip_fields:
            ini_value = getattr(cobject, to_strip_field)
            if isinstance(ini_value, str):
                setattr(cobject, to_strip_field, ini_value.strip() or False)
        time_values_allowed = ("morning", "afternoon", "evening")
        arrival_time = cobject.arrival_time
        if arrival_time not in time_values_allowed:
            error_msg = (
                f"Wrong arrival time: {arrival_time}. "
                f"Possible values: {', '.join(time_values_allowed)}."
            )
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
            )
        departure_time = cobject.departure_time
        if departure_time not in time_values_allowed:
            error_msg = (
                f"Wrong departure time: {departure_time}. "
                f"Possible values: {', '.join(time_values_allowed)}."
            )
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
            )
        notes_list = cobject.notes_list
        if not isinstance(notes_list, list):
            notes_list = []
        lastname = cobject.lastname
        if not lastname:  # Should never happen because checked by fastapi
            logger.error("Missing lastname in stay controller. Quitting.")
            return False
        partner_name = lastname
        firstname = cobject.firstname
        if firstname:
            partner_name = f"{firstname} {partner_name}"
        title = cobject.title
        if title:
            title2label = {
                "mister": "M.",
                "madam": "Mme",
                "miss": "Mlle",
            }
            if title in title2label:
                partner_name = f"{title2label[title]} {partner_name}"
            else:
                logger.warning("Bad value for title: %s", title)
                title = False
        email = cobject.email
        if not email:  # Should never happen because defined as required
            logger.error("Missing email in stay controller. Quitting.")
        # country
        country_id = False
        if cobject.country_code:
            country_code = cobject.country_code.upper()
            country = self.env["res.country"].search_read(
                [("code", "=", country_code)], ["id"], limit=1
            )
            if country:
                country_id = country[0]["id"]
            else:
                logger.warning("Country code %s doesn't exist in Odoo.", country_code)
                notes_list.append(
                    _("Country code %s doesn't exist in Odoo.") % country_code
                )

        vals = {
            "partner_name": partner_name,
            "arrival_time": arrival_time,
            "arrival_note": cobject.arrival_note,
            "departure_time": departure_time,
            "departure_note": cobject.departure_note,
            "controller_message": cobject.message,
            "controller_firstname": firstname,
            "controller_lastname": lastname,
            "controller_email": email,
            "controller_phone": cobject.phone,
            "controller_mobile": cobject.mobile,
            "controller_title": title,
            "controller_street": cobject.street,
            "controller_street2": cobject.street2,
            "controller_zip": cobject.zip,
            "controller_city": cobject.city,
            "controller_country_id": country_id,
            "controller_notes": "\n".join(notes_list),
        }
        if try_match_partner:
            if "res.partner.phone" in self.env:  # module base_partner_one2many_phone
                partner_phone = (
                    self.env["res.partner.phone"]
                    .sudo()
                    .search_read(
                        [
                            ("type", "in", ("1_email_primary", "2_email_secondary")),
                            ("email", "=ilike", email),
                            ("partner_id", "!=", False),
                        ],
                        ["partner_id"],
                        limit=1,
                    )
                )
                vals["partner_id"] = (
                    partner_phone and partner_phone[0]["partner_id"][0] or None
                )
            else:
                partner = self.env["res.partner"].search_read(
                    [("email", "=ilike", email)], ["id"], limit=1
                )
                vals["partner_id"] = partner and partner[0]["id"] or None
        return vals
