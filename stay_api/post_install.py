# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from uuid import uuid4

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def stay_api_postinstall(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        logger.info("Starting to write uuid on stays")
        stays = env["stay.stay"].search([("controller_uuid", "=", False)])
        for stay in stays:
            stay.write({"controller_uuid": str(uuid4())})
        logger.info("%d stays updated with uuid", len(stays))
        # also set stay_code on res.partner.title
        model_datas = env["ir.model.data"].search(
            [
                ("module", "=", "base"),
                ("model", "=", "res.partner.title"),
                ("res_id", "!=", False),
                ("name", "!=", False),
            ]
        )
        unique_code = set()
        for model_data in model_datas:
            stay_code = model_data.name.split("_")[-1]
            if stay_code in unique_code:
                logger.warning(
                    "Skipping XMLID %s.%s because the suffix is not unique",
                    model_data.module,
                    model_data.name,
                )
                continue
            unique_code.add(stay_code)
            title = env["res.partner.title"].browse(model_data.res_id)
            title.write({"stay_code": stay_code})
            logger.info(
                "Wrote stay_code=%s on title %s ID %d",
                stay_code,
                title.display_name,
                title.id,
            )
