# Copyright 2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StayStay(models.Model):
    _inherit = "stay.stay"

    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Company Currency",
        store=True,
    )
    donation_total = fields.Monetary(
        compute="_compute_donation",
        currency_field="company_currency_id",
        help="Total donation amount for draft and valid donations in company currency.",
        store=True,
    )
    donation_count = fields.Integer(
        compute="_compute_donation", store=True, string="Number of Donations"
    )
    donation_ids = fields.One2many("donation.donation", "stay_id", string="Donations")

    @api.depends("donation_ids.state", "donation_ids.amount_total_company_currency")
    def _compute_donation(self):
        rg_res = self.env["donation.donation"].read_group(
            [("stay_id", "in", self.ids), ("state", "in", ("draft", "done"))],
            ["stay_id", "amount_total_company_currency:sum"],
            ["stay_id"],
        )
        mapped_data = {
            x["stay_id"][0]: {
                "total": x["amount_total_company_currency"],
                "count": x["stay_id_count"],
            }
            for x in rg_res
        }
        for stay in self:
            stay.donation_total = mapped_data.get(stay.id, {"total": 0})["total"]
            stay.donation_count = mapped_data.get(stay.id, {"count": 0})["count"]

    def show_donations(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("donation.donation_action")
        if self.donation_count == 1:
            action.update(
                {
                    "res_id": self.donation_ids.id,
                    "views": False,
                    "view_id": False,
                    "view_mode": "form,tree,pivot,graph",
                }
            )
        else:
            action["domain"] = [("stay_id", "=", self.id)]
        return action
