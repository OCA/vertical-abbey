# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import sys
from datetime import date, datetime, timedelta

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from odoo import _, api, tools

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import (
    authenticated_partner,
    authenticated_partner_env,
)

from ..schemas import StayCreated, StayInput

logger = logging.getLogger(__name__)


stay_api_router = APIRouter()


@stay_api_router.post("/new", response_model=StayCreated, status_code=201)
def stay_new(  # noqa: C901
    env: Annotated[api.Environment, Depends(authenticated_partner_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    stayinput: StayInput,
) -> StayCreated:
    logger.debug("Start stay create controller stayinput=%s", stayinput)
    sso = env["stay.stay"]
    company_id = stayinput.company_id
    if not company_id:
        company_str = (
            env["ir.config_parameter"]
            .sudo()
            .get_param("stay.controller.company_id", False)
        )
        if company_str:
            try:
                company_id = int(company_str)
            except Exception as e:
                logger.warning(
                    "Failed to convert ir.config_parameter "
                    "stay.controller.company_id %s to int: %s",
                    company_str,
                    e,
                )
    if not company_id:
        company_id = env.ref("base.main_company").id
    # protection for DoS attacks
    limit_create_date = datetime.now() - timedelta(1)
    recent_draft_stay = sso.search_count(
        [
            ("company_id", "=", company_id),
            ("create_date", ">=", limit_create_date),
            ("state", "=", "draft"),
        ]
    )
    recent_draft_stay_limit_str = (
        env["ir.config_parameter"]
        .sudo()
        .get_param("stay.controller.max_requests_24h", 100)
    )
    recent_draft_stay_limit = int(recent_draft_stay_limit_str)
    logger.debug("recent_draft_stay=%d", recent_draft_stay)
    if recent_draft_stay > recent_draft_stay_limit and not tools.config.get(
        "test_enable"
    ):
        logger.error(
            "stay controller: %d draft stays created during the last 24h. "
            "Suspecting DoS attack. Request ignored.",
            recent_draft_stay,
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)

    # strip all string values
    to_strip_fields = [
        "firstname",
        "lastname",
        "street",
        "street2",
        "zip",
        "city",
        "country_code",
        "email",
        "mobile",
        "departure_note",
        "arrival_note",
    ]
    for to_strip_field in to_strip_fields:
        ini_value = getattr(stayinput, to_strip_field)
        if isinstance(ini_value, str):
            setattr(stayinput, to_strip_field, ini_value.strip() or False)
    arrival_date = stayinput.arrival_date
    departure_date = stayinput.departure_date
    if arrival_date < date.today():
        error_msg = f"Arrival date {arrival_date} cannot be in the past"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
        )
    if departure_date < arrival_date:
        error_msg = (
            f"Departure date {departure_date} cannot be before "
            f"arrival date {arrival_date}"
        )
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
        )
    time_values_allowed = ("morning", "afternoon", "evening")
    arrival_time = stayinput.arrival_time
    if arrival_time not in time_values_allowed:
        error_msg = (
            f"Wrong arrival time: {arrival_time}. "
            f"Possible values: {', '.join(time_values_allowed)}."
        )
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
        )
    departure_time = stayinput.departure_time
    if departure_time not in time_values_allowed:
        error_msg = (
            f"Wrong departure time: {departure_time}. "
            f"Possible values: {', '.join(time_values_allowed)}."
        )
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
        )
    guest_qty = stayinput.guest_qty
    if guest_qty < 1:
        error_msg = f"Guest quantity ({guest_qty}) must be strictly positive."
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
        )
    notes_list = stayinput.notes_list
    if not isinstance(notes_list, list):
        notes_list = []
    lastname = stayinput.lastname
    if not lastname:  # Should never happen because checked by fastapi
        logger.error("Missing lastname in stay controller. Quitting.")
        return False
    partner_name = lastname
    firstname = stayinput.firstname
    if firstname:
        partner_name = f"{firstname} {partner_name}"
    title = stayinput.title
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
    email = stayinput.email
    if not email:  # Should never happen because defined as required
        logger.error("Missing email in stay controller. Quitting.")
        return False
    if "res.partner.phone" in env:  # module base_partner_one2many_phone
        partner_phone = (
            env["res.partner.phone"]
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
        partner_id = partner_phone and partner_phone[0]["partner_id"][0] or None
    else:
        partner = env["res.partner"].search_read(
            [("email", "=ilike", email)], ["id"], limit=1
        )
        partner_id = partner and partner[0]["id"] or None
    # country
    country_id = False
    if stayinput.country_code:
        country_code = stayinput.country_code.upper()
        country = env["res.country"].search_read(
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
        "controller": True,
        "company_id": company_id,
        "group_id": stayinput.group_id or False,
        "guest_qty": guest_qty,
        "partner_name": partner_name,
        "partner_id": partner_id,
        "arrival_date": arrival_date,
        "arrival_time": arrival_time,
        "arrival_note": stayinput.arrival_note,
        "departure_date": departure_date,
        "departure_time": departure_time,
        "departure_note": stayinput.departure_note,
        "controller_notes": stayinput.notes,
        "controller_firstname": firstname,
        "controller_lastname": lastname,
        "controller_email": email,
        "controller_mobile": stayinput.mobile,
        "controller_title": title,
        "controller_street": stayinput.street,
        "controller_street2": stayinput.street2,
        "controller_zip": stayinput.zip,
        "controller_city": stayinput.city,
        "controller_country_id": country_id,
        "notes": "\n".join(notes_list),
    }
    logger.debug("Creating new stay with vals=%s", vals)
    stay = sso.create(vals)
    logger.info("Create stay %s ID %d from controller", stay.display_name, stay.id)
    try:
        env.ref("stay_api.stay_created_by_controller_notify").sudo().send_mail(stay.id)
        logger.info("Mail sent for new stay notification")
    except Exception as e:
        logger.error("Failed to generate new stay email: %s", e)
    return StayCreated(
        name=stay.name, id=stay.id, company_id=company_id, partner_id=partner_id
    )
