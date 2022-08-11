# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class MassRequest(models.Model):
    _inherit = "mass.request"

    donation_line_id = fields.Many2one(
        'donation.line', string='Related Donation Line', readonly=True)
    donation_id = fields.Many2one(
        'donation.donation', related='donation_line_id.donation_id',
        string="Related Donation", readonly=True, store=True)
