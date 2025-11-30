# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stay_default_refectory_id = fields.Many2one(
        related="company_id.default_refectory_id", readonly=False
    )
    group_stay_breakfast = fields.Boolean(
        string="Manage Breakfast", implied_group="stay.group_stay_breakfast"
    )
    stay_room_transition = fields.Selection(
        [
            ("one_empty_period", "One Empty Period"),
            ("immediate", "Immediate"),
            ("night", "Night"),
        ],
        string="Room Transition",
        config_parameter="stay.room_transition",
    )
    stay_notify_user_ids = fields.Many2many(
        related="company_id.stay_notify_user_ids", readonly=False
    )
