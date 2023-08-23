# Copyright 2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    donation_stay_product_id = fields.Many2one(
        "product.product",
        string="Product for Stay Donations",
        ondelete="restrict",
        domain=[("detailed_type", "=", "donation")],
    )
    donation_stay_campaign_id = fields.Many2one(
        "donation.campaign", string="Campaign for Stay Donations", ondelete="restrict"
    )
