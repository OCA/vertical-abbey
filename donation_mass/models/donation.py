# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class DonationDonation(models.Model):
    _inherit = "donation.donation"

    mass_request_ids = fields.One2many(
        "mass.request", "donation_id", string="Masses", readonly=True
    )
    mass_request_count = fields.Integer(
        compute="_compute_mass_request_count", string="# of Mass Requests"
    )

    def _compute_mass_request_count(self):
        rg_res = self.env["mass.request"].read_group(
            [("donation_id", "in", self.ids)], ["donation_id"], ["donation_id"]
        )
        mapped_data = {x["donation_id"][0]: x["donation_id_count"] for x in rg_res}
        for donation in self:
            donation.mass_request_count = mapped_data.get(donation.id, 0)

    def validate(self):
        res = super().validate()
        mro = self.env["mass.request"]
        for donation in self:
            for line in donation.line_ids:
                if line.product_id.detailed_type == "donation_mass":
                    mro.sudo().create(line._prepare_mass_request())
        return res

    def done2cancel(self):
        for donation in self:
            mass_requests = self.env["mass.request"].search(
                [("donation_id", "=", donation.id)]
            )
            if mass_requests:
                for mass_request in mass_requests:
                    if mass_request.state != "waiting":
                        raise UserError(
                            _(
                                "Cannot cancel the donation '%(donation)s' "
                                "because it is linked to a mass request in "
                                "%(mass_state)s state.",
                                donation=donation.display_name,
                                mass_state=mass_request._fields[
                                    "state"
                                ].convert_to_export(mass_request.state, mass_request),
                            )
                        )
                self.message_post(
                    body=_(
                        "%d related mass request(s) in waiting state "
                        "have been deleted."
                    )
                    % len(mass_requests)
                )
                mass_requests.sudo().unlink()
        return super().done2cancel()

    def goto_mass_requests(self):
        self.ensure_one()
        assert self.mass_request_ids
        action = self.env["ir.actions.actions"]._for_xml_id("mass.mass_request_action")
        if len(self.mass_request_ids) == 1:
            action.update(
                {
                    "view_mode": "form,tree,pivot,graph",
                    "views": False,
                    "res_id": self.mass_request_ids.id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "tree,form,pivot,graph",
                    "views": False,
                    "domain": [("donation_id", "=", self.id)],
                }
            )
        return action

    def _prepare_donation_move(self):
        """Remove analytic distrib on mass lines:
        we don't put analytic on stock accounts"""
        vals = super()._prepare_donation_move()
        ppo = self.env["product.product"]
        if vals:
            for line in vals.get("line_ids", []):
                lvals = line[2]
                if (
                    lvals.get("display_type") == "product"
                    and lvals.get("product_id")
                    and lvals.get("analytic_distribution")
                ):
                    product = ppo.browse(lvals["product_id"])
                    if product.detailed_type == "donation_mass":
                        lvals["analytic_distribution"] = False
        return vals


class DonationLine(models.Model):
    _inherit = "donation.line"

    celebrant_id = fields.Many2one(
        "res.partner",
        ondelete="restrict",
        domain=[("celebrant", "=", "internal")],
    )
    mass_request_date = fields.Date(string="Celebration Requested Date")
    intention = fields.Char()
    mass_request_ids = fields.One2many(
        "mass.request", "donation_line_id", string="Masses"
    )

    def _prepare_mass_request(self):
        self.ensure_one()
        donation = self.donation_id
        company = donation.company_id
        if not company.mass_stock_account_id:
            raise UserError(
                _("Missing mass stock account on company '%s'.") % company.display_name
            )
        vals = {
            "partner_id": donation.partner_id.id,
            "celebrant_id": self.celebrant_id.id or False,
            "donation_date": donation.donation_date,
            "request_date": self.mass_request_date or False,
            "product_id": self.product_id.id,
            "offering": self.amount_company_currency,
            "stock_account_id": company.mass_stock_account_id.id,
            "analytic_distribution": self.analytic_distribution or False,
            "quantity": self.quantity,
            "intention": self.intention,
            "donation_line_id": self.id,
            "company_id": company.id,
        }
        return vals

    def _get_account(self):
        if self.product_id.detailed_type == "donation_mass":
            if not self.company_id.mass_stock_account_id:
                raise UserError(
                    _("Missing mass stock account on company '%s'.")
                    % self.company_id.display_name
                )
            return self.company_id.mass_stock_account_id
        return super()._get_account()
