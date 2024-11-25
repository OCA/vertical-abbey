# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo.tests.common import TransactionCase


class TestDonationFromStay(TransactionCase):
    def test_donate_from_stay(self):
        company = self.env.ref("base.main_company")
        if not company.donation_stay_product_id:
            stay_product = self.env["product.product"].create(
                {
                    "name": "Stay Donation",
                    "detailed_type": "donation",
                    "categ_id": self.env.ref("product.product_category_all").id,
                    "taxes_id": False,
                    "supplier_taxes_id": False,
                }
            )
            company.write({"donation_stay_product_id": stay_product.id})
        today = datetime.now().date()
        tomorrow = today + relativedelta(days=1)
        refectory_id = (
            self.env["stay.refectory"].create({"name": "test donation_stay"}).id
        )
        partner = self.env["res.partner"].create({"name": "Ophélie Hiver"})
        stay = self.env["stay.stay"].create(
            {
                "arrival_date": today,
                "arrival_time": "afternoon",
                "departure_date": tomorrow,
                "departure_time": "afternoon",
                "partner_id": partner.id,
                "guest_qty": 2,
                "refectory_id": refectory_id,
                "company_id": company.id,
            }
        )
        stay.draft2confirm()
        dsco = self.env["donation.stay.create"]
        bank_journal = self.env["account.journal"].create(
            {
                "type": "bank",
                "name": "test bank journal",
                "company_id": company.id,
            }
        )
        payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "test_payment_mode",
                "donation": True,
                "bank_account_link": "fixed",
                "fixed_journal_id": bank_journal.id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "company_id": company.id,
            }
        )
        payment_ref = "CHQ LBP 421242"
        wiz = dsco.with_context(
            active_id=stay.id,
            active_ids=[stay.id],
            active_model="stay.stay",
        ).create(
            {
                "payment_mode_id": payment_mode.id,
                "amount": 200,
                "payment_ref": payment_ref,
            }
        )
        action = wiz.create_donation()
        donation_id = action["res_id"]
        donation = self.env["donation.donation"].browse(donation_id)
        self.assertEqual(len(donation.line_ids), 1)
        self.assertEqual(donation.state, "draft")
        self.assertEqual(donation.company_id, stay.company_id)
        self.assertEqual(
            donation.line_ids[0].product_id, stay.company_id.donation_stay_product_id
        )
        self.assertEqual(
            donation.campaign_id, stay.company_id.donation_stay_campaign_id
        )
        self.assertEqual(donation.stay_id, stay)
        self.assertEqual(donation.amount_total, 200)
        self.assertEqual(donation.partner_id, stay.partner_id)
        donation.validate()
        self.assertEqual(donation.move_id.state, "posted")
        self.assertEqual(donation.payment_mode_id, payment_mode)
        self.assertEqual(donation.payment_ref, payment_ref)
