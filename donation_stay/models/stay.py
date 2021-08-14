# Copyright 2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StayStay(models.Model):
    _inherit = "stay.stay"

    donation_id = fields.Many2one(
        "donation.donation", string="Donation", readonly=True, copy=False, tracking=True
    )
