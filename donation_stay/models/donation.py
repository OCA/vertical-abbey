# Copyright 2024 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DonationDonation(models.Model):
    _inherit = "donation.donation"

    stay_id = fields.Many2one(
        "stay.stay",
        string="Stay",
        copy=False,
        tracking=True,
        check_company=True,
        domain=[("state", "!=", "draft")],
    )
