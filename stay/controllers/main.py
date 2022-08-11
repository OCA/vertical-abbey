# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Matthieu Dubois <dubois.matthieu@tutanota.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request


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
        partner_name = kwargs.get("partner_name")
        if kwargs.get("title"):
            title2label = {
                "mister": "M.",
                "madam": "Mme",
                "miss": "Mlle",
            }
            partner_name = "%s %s" % (title2label.get(kwargs["title"]), partner_name)
        partner = request.env["res.partner"].search(
            [("email", "=ilike", kwargs.get("email"))]
        )
        partner_id = partner and partner.id or False
        notes = f"{kwargs.get('notes')}\n{kwargs.get('mobile')}\n{kwargs.get('email')}"
        stay = (
            request.env["stay.stay"]
            .sudo()
            .create(
                {
                    "guest_qty": kwargs.get("guest_qty"),
                    "partner_name": partner_name,
                    "partner_id": partner_id,
                    "arrival_date": kwargs.get("arrival_date"),
                    "arrival_time": kwargs.get("arrival_time"),
                    "departure_date": kwargs.get("departure_date"),
                    "departure_time": kwargs.get("departure_time"),
                    "notes": notes,
                }
            )
        )
        vals = {
            "stay": stay,
            "main_object": stay,
        }
        res = request.render("stay.stay_saved_iframe", vals)
        # TODO add mail confirmation
        return res
