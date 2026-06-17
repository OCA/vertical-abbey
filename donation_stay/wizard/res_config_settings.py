# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    donation_stay_product_id = fields.Many2one(
        related="company_id.donation_stay_product_id", readonly=False
    )
    donation_stay_campaign_id = fields.Many2one(
        related="company_id.donation_stay_campaign_id", readonly=False
    )
