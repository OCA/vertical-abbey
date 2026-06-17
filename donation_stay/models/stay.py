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
        rg_res = self.env["donation.donation"]._read_group(
            [("stay_id", "in", self.ids), ("state", "in", ("draft", "done"))],
            aggregates=["__count", "amount_total_company_currency:sum"],
            groupby=["stay_id"],
        )
        mapped_data = {
            stay.id: {"count": stay_count, "total": amount_total}
            for (stay, stay_count, amount_total) in rg_res
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
                    "view_mode": "form,list,pivot,graph",
                }
            )
        else:
            action["domain"] = [("stay_id", "=", self.id)]
        return action
