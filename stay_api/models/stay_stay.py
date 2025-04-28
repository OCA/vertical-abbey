# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StayStay(models.Model):
    _inherit = "stay.stay"

    controller = fields.Boolean(readonly=True, string="Created from Web Form")
    controller_firstname = fields.Char(tracking=True, string="Firstname")
    controller_lastname = fields.Char(tracking=True, string="Lastname")
    controller_title = fields.Selection(
        [
            ("mister", "Mister"),
            ("madam", "Madam"),
            ("miss", "Miss"),
        ],
        tracking=True,
        string="Title",
    )
    controller_email = fields.Char(tracking=True, string="E-mail")
    controller_mobile = fields.Char(tracking=True, string="Mobile")
    controller_notes = fields.Text(string="Web Form Notes")
    controller_street = fields.Char(string="Address Line 1")
    controller_street2 = fields.Char(string="Address Line 2")
    controller_zip = fields.Char(string="ZIP")
    controller_city = fields.Char(string="City")
    controller_country_id = fields.Many2one("res.country", string="Country")
