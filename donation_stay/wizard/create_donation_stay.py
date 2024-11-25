# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Brother Irénée
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DonationStayCreate(models.TransientModel):
    _name = "donation.stay.create"
    _description = "Create Donation from a Stay"

    stay_id = fields.Many2one("stay.stay", string="Stay", required=True)
    company_id = fields.Many2one("res.company", string="Company", required=True)
    partner_id = fields.Many2one("res.partner", string="Guest", required=True)
    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        string="Payment Mode",
        required=True,
        domain="[('donation', '=', True), ('company_id', '=', company_id)]",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(
        string="Donation Amount", currency_field="currency_id", required=True
    )
    date_donation = fields.Date(
        "Donation Date", required=True, default=fields.Date.context_today
    )
    payment_ref = fields.Char("Payment Reference")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert self._context.get("active_model") == "stay.stay"
        stay = self.env["stay.stay"].browse(self._context.get("active_id"))
        res.update(
            {
                "stay_id": stay.id,
                "company_id": stay.company_id.id,
                "partner_id": stay.partner_id.id or False,
            }
        )
        return res

    def _prepare_donation(self):
        if self.currency_id.compare_amounts(self.amount, 0) <= 0:
            raise UserError(_("The amount of the donation is not set or negative."))
        company = self.company_id
        assert self.stay_id.company_id == company
        campaign_id = company.donation_stay_campaign_id.id or False
        stay_donation_product = company.donation_stay_product_id
        if not stay_donation_product:
            raise UserError(
                _("Donation Stay Product not set on company '%s'.")
                % company.display_name
            )
        line_vals = {
            "product_id": stay_donation_product.id,
            "quantity": 1,
            "unit_price": self.amount,
        }
        vals = {
            "stay_id": self.stay_id.id,
            "partner_id": self.partner_id.id,
            "payment_mode_id": self.payment_mode_id.id,
            "currency_id": self.currency_id.id,
            "payment_ref": self.payment_ref,
            "check_total": self.amount,
            "donation_date": self.date_donation,
            "campaign_id": campaign_id,
            "line_ids": [(0, 0, line_vals)],
            "company_id": self.company_id.id,
            "tax_receipt_option": self.partner_id.commercial_partner_id.tax_receipt_option,
        }
        return vals

    def create_donation(self):
        self.ensure_one()
        donation_vals = self._prepare_donation()
        donation = self.env["donation.donation"].create(donation_vals)
        donation.message_post(
            body=_(
                "Donation created from stay "
                "<a href=# data-oe-model=stay.stay data-oe-id=%(stay_id)s>%(stay)s</a>.",
                stay_id=self.stay_id.id,
                stay=self.stay_id.display_name,
            )
        )
        action = self.env["ir.actions.actions"]._for_xml_id("donation.donation_action")
        action.update(
            {
                "views": False,
                "view_mode": "form,tree,pivot,graph",
                "res_id": donation.id,
            }
        )
        return action
