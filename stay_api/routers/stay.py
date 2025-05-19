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

from ..schemas import StayCreate, StayCreated, StayMatch, StayRead, StayUpdate

logger = logging.getLogger(__name__)

stay_api_router = APIRouter()


@stay_api_router.post("/new", response_model=StayCreated, status_code=201)
def stay_new(
    env: Annotated[api.Environment, Depends(authenticated_partner_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    staycreate: StayCreate,
) -> StayCreated:
    logger.debug("Start stay create controller staycreate=%s", staycreate)
    sso = env["stay.stay"]
    company_id = staycreate.company_id
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

    vals = sso._controller_prepare_create_update(staycreate)
    if not vals:
        return False

    arrival_date = staycreate.arrival_date
    departure_date = staycreate.departure_date
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
    guest_qty = staycreate.guest_qty
    if guest_qty < 1:
        error_msg = f"Guest quantity ({guest_qty}) must be strictly positive."
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_msg
        )

    vals.update(
        {
            "controller_mode": "created",
            "company_id": company_id,
            "group_id": staycreate.group_id or False,
            "guest_qty": guest_qty,
            "arrival_date": arrival_date,
            "departure_date": departure_date,
        }
    )
    logger.debug("Creating new stay with vals=%s", vals)
    stay = sso.create(vals)
    logger.info("Create stay %s ID %d from controller", stay.display_name, stay.id)
    try:
        env.ref("stay_api.stay_controller_notify").sudo().with_context(
            action_description=_("created")
        ).send_mail(stay.id)
        logger.info("Mail sent for stay creation notification")
    except Exception as e:
        logger.error("Failed to generate stay creation email: %s", e)
    return StayCreated(
        name=stay.name,
        id=stay.id,
        company_id=vals["company_id"],
        partner_id=vals["partner_id"],
        uuid=stay.controller_uuid,
    )


@stay_api_router.get("/cancel")
def stay_cancel(
    env: Annotated[api.Environment, Depends(authenticated_partner_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    staymatch: StayMatch,
):
    logger.debug("Start stay cancel controller staymatch=%s", staymatch)
    stay = env["stay.stay"]._get_stay_from_uuid(
        staymatch.uuid, "/cancel", ignore_states=("cancel", "done")
    )
    if stay:
        logger.info("Cancelling stay %s currently in %s state", stay.name, stay.state)
        stay.cancel()
        stay.message_post(body=_("Stay cancelled by API call."))
        try:
            env.ref("stay_api.stay_controller_notify").sudo().with_context(
                action_description=_("cancelled")
            ).send_mail(stay.id)
            logger.info("Mail sent for stay cancellation notification")
        except Exception as e:
            logger.error("Failed to generate stay cancellation email: %s", e)


@stay_api_router.get("/read", response_model=StayRead)
def stay_read(
    env: Annotated[api.Environment, Depends(authenticated_partner_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    staymatch: StayMatch,
) -> StayRead:
    logger.debug("Start stay read controller staymatch=%s", staymatch)
    stay = env["stay.stay"]._get_stay_from_uuid(
        staymatch.uuid, "/read", raise_states=("cancel", "done")
    )
    if stay:
        vals = {
            "name": stay.name,
            "guest_qty": stay.guest_qty,
            "arrival_date": stay.arrival_date,
            "departure_date": stay.departure_date,
        }
        if stay.arrival_time != "unknown":
            vals["arrival_time"] = stay.arrival_time
        if stay.departure_time != "unknown":
            vals["departure_time"] = stay.departure_time
        if stay.partner_id:
            vals.update(
                {
                    "street": stay.partner_id.street or None,
                    "street2": stay.partner_id.street2 or None,
                    "zip": stay.partner_id.zip or None,
                    "city": stay.partner_id.city or None,
                    "country_code": stay.partner_id.country_id
                    and stay.partner_id.country_id.code
                    or None,
                    "phone": stay.partner_id.phone or None,
                    "mobile": stay.partner_id.mobile or None,
                    "email": stay.partner_id.email or None,
                    "partner_name": stay.partner_id.name,
                }
            )
            if hasattr(stay.partner_id, "firstname"):
                vals.update(
                    {
                        "firstname": stay.partner_id.firstname,
                        "lastname": stay.partner_id.lastname,
                    }
                )
            if stay.partner_id.title and stay.partner_id.title.stay_code:
                vals["title"] = stay.partner_id.title.stay_code
        return StayRead(**vals)


@stay_api_router.post("/update")
def stay_update(
    env: Annotated[api.Environment, Depends(authenticated_partner_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
    stayupdate: StayUpdate,
):
    logger.debug("Start stay update controller stayupdate=%s", stayupdate)
    stay = env["stay.stay"]._get_stay_from_uuid(
        stayupdate.uuid, "/update", raise_states=("cancel", "done")
    )
    if stay:
        try_match_partner = True
        if stay.partner_id:
            try_match_partner = False
        vals = env["stay.stay"]._controller_prepare_create_update(
            stayupdate, try_match_partner=try_match_partner
        )
        if not vals:
            return False
        vals.update(
            {
                "controller_mode": "updated",
            }
        )
        logger.debug("Updating stay %s ID %s with vals=%s", stay.name, stay.id, vals)
        stay.write(vals)
        try:
            env.ref("stay_api.stay_controller_notify").sudo().with_context(
                action_description=_("updated")
            ).send_mail(stay.id)
            logger.info("Mail sent for stay update notification")
        except Exception as e:
            logger.error("Failed to generate stay update email: %s", e)
