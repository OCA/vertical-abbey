# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from uuid import uuid4

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def stay_set_uuid(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        logger.info("Starting to write uuid on stays")
        stays = env["stay.stay"].search([])
        for stay in stays:
            stay.write({"controller_uuid": str(uuid4())})
        logger.info("%d stays updated with uuid", len(stays))
