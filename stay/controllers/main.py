# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Matthieu Dubois <dubois.matthieu@tutanota.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta

from odoo import _, http, tools
from odoo.http import request

logger = logging.getLogger(__name__)


class StayController(http.Controller):

    # To make it work, you need to set db_name and dbfilter in your odoo server
    # config file
    # Don't forget to also set proxy_mode = True
    @http.route("/stay/new", type="http", auth="public", website=True, csrf=False)
    def stay_new(self, **kwargs):
        res = request.render("stay.stay_form_iframe", {})
        return res

    @http.route(
        "/stay/saved",
        type="http",
        methods=["POST"],
        auth="public",
        website=True,
        csrf=False,
    )
    def stay_saved(self, **kwargs):
        sso = request.env["stay.stay"].sudo()
        company_id = kwargs.get("company_id")
        if not company_id:
            company_str = (
                request.env["ir.config_parameter"]
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
            company_id = request.env.ref("base.main_company").id
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
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("stay.controller.max_requests_24h", 100)
        )
        recent_draft_stay_limit = int(recent_draft_stay_limit_str)
        logger.debug("recent_draft_stay=%d", recent_draft_stay)
        if recent_draft_stay > recent_draft_stay_limit and not tools.config.test_enable:
            logger.error(
                "stay controller: %d draft stays created during the last 24h. "
                "Suspecting DoS attack. Request ignored.",
                recent_draft_stay,
            )
            return False

        # strip all string values
        for key, value in kwargs.items():
            if isinstance(value, str):
                kwargs[key] = value.strip() or False
        notes_list = kwargs.get("notes_list")
        if not isinstance(notes_list, list):
            notes_list = []
        lastname = kwargs.get("lastname")
        if not lastname:
            logger.error("Missing lastname in stay controller. Quitting.")
            return False
        partner_name = lastname
        firstname = kwargs.get("firstname")
        if firstname:
            partner_name = f"{firstname} {partner_name}"
        title = False
        if kwargs.get("title"):
            title2label = {
                "mister": "M.",
                "madam": "Mme",
                "miss": "Mlle",
            }
            if kwargs["title"] in title2label:
                title = kwargs["title"]
                partner_name = f"{title2label[kwargs['title']]} {partner_name}"
        email = kwargs.get("email")
        if not email:
            logger.error("Missing email in stay controller. Quitting.")
            return False
        partner = request.env["res.partner"].search(
            [("email", "=ilike", email)], limit=1
        )
        partner_id = partner and partner.id or False
        # country
        country_id = False
        if kwargs.get("country_code"):
            country_code = kwargs["country_code"].upper()
            country = (
                request.env["res.country"]
                .sudo()
                .search_read([("code", "=", country_code)], ["id"], limit=1)
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
            "group_id": kwargs.get("group_id"),
            "guest_qty": kwargs.get("guest_qty"),
            "partner_name": partner_name,
            "partner_id": partner_id,
            "arrival_date": kwargs.get("arrival_date"),
            "arrival_time": kwargs.get("arrival_time"),
            "arrival_note": kwargs.get("arrival_note"),
            "departure_date": kwargs.get("departure_date"),
            "departure_time": kwargs.get("departure_time"),
            "departure_note": kwargs.get("departure_note"),
            "controller_notes": kwargs.get("notes"),
            "controller_firstname": firstname,
            "controller_lastname": lastname,
            "controller_email": email,
            "controller_mobile": kwargs.get("mobile"),
            "controller_title": title,
            "controller_street": kwargs.get("street"),
            "controller_street2": kwargs.get("street2"),
            "controller_zip": kwargs.get("zip"),
            "controller_city": kwargs.get("city"),
            "controller_country_id": country_id,
            "notes": "\n".join(notes_list),
        }
        logger.debug("Creating new stay with vals=%s", vals)
        stay = sso.create(vals)
        logger.info("Create stay %s ID %d from controller", stay.display_name, stay.id)
        try:
            request.env.ref("stay.stay_created_by_controller_notify").sudo().send_mail(
                stay.id
            )
            logger.info("Mail sent for new stay notification")
        except Exception as e:
            logger.error("Failed to generate new stay email: %s", e)
        vals = {
            "stay": stay,
            "main_object": stay,
        }
        res = request.render("stay.stay_saved_iframe", vals)
        return res
