# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestDonationFromStay(TransactionCase):
    def test_donate_from_stay(self):
        stay = self.env.ref("stay.stay2")
        dsco = self.env["donation.stay.create"]
        ctx = {
            "active_id": stay.id,
            "active_ids": [stay.id],
            "active_model": "stay.stay",
        }
        bank_journal = self.env["account.journal"].create(
            {
                "type": "bank",
                "name": "test bank journal",
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
            }
        )
        payment_ref = "CHQ LBP 421242"
        wiz = dsco.with_context(ctx).create(
            {
                "payment_mode_id": payment_mode.id,
                "amount": 200,
                "payment_ref": payment_ref,
            }
        )
        action = wiz.create_donation()
        donation_id = action["res_id"]
        donation = self.env["donation.donation"].browse(donation_id)
        self.assertEqual(donation.state, "draft")
        self.assertEqual(
            donation.campaign_id, stay.company_id.donation_stay_campaign_id
        )
        self.assertEqual(stay.donation_id, donation)
        self.assertEqual(donation.amount_total, 200)
        self.assertEqual(
            donation.partner_id, self.env.ref("base.res_partner_address_2")
        )
        donation.validate()
        self.assertEqual(donation.move_id.state, "posted")
        self.assertEqual(donation.payment_mode_id, payment_mode)
        self.assertEqual(donation.payment_ref, payment_ref)
