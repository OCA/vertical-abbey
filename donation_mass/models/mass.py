# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MassRequest(models.Model):
    _inherit = "mass.request"

    donation_line_id = fields.Many2one(
        "donation.line", string="Related Donation Line", readonly=True
    )
    donation_id = fields.Many2one(
        related="donation_line_id.donation_id", string="Related Donation", store=True
    )
