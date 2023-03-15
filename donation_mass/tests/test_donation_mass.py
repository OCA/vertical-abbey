# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

from odoo.tests.common import SavepointCase


class TestDonationMass(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.bank_journal = cls.env["account.journal"].create(
            {
                "type": "bank",
                "name": "test bank journal",
            }
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "test_payment_mode_donation_mass",
                "donation": True,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.bank_journal.id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
            }
        )
        today = time.strftime("%Y-%m-%d")
        cls.ddo = cls.env["donation.donation"]
        cls.donor1 = cls.env.ref("donation_base.donor1")
        cls.donor2 = cls.env.ref("donation_base.donor2")
        cls.donor3 = cls.env.ref("donation_base.donor3")

        cls.don1 = cls.ddo.create(
            {
                "check_total": 17,
                "partner_id": cls.donor1.id,
                "donation_date": today,
                "payment_mode_id": cls.payment_mode.id,
                "tax_receipt_option": "each",
                "payment_ref": "CHQ CA 229026",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref(
                                "mass.product_product_mass_simple"
                            ).id,
                            "quantity": 1,
                            "unit_price": 17,
                            "intention": "For my grand-mother",
                        },
                    )
                ],
            }
        )
        cls.don2 = cls.ddo.create(
            {
                "check_total": 340,
                "partner_id": cls.donor2.id,
                "donation_date": today,
                "payment_mode_id": cls.payment_mode.id,
                "tax_receipt_option": "each",
                "payment_ref": "CHQ BP 9087123",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref(
                                "mass.product_product_mass_novena"
                            ).id,
                            "quantity": 2,
                            "unit_price": 170,
                            "intention": "For my father",
                        },
                    )
                ],
            }
        )
        cls.don3 = cls.ddo.create(
            {
                "check_total": 540,
                "partner_id": cls.donor3.id,
                "donation_date": today,
                "payment_mode_id": cls.payment_mode.id,
                "tax_receipt_option": "each",
                "payment_ref": "CHQ HSBC 98302217",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref(
                                "mass.product_product_mass_gregorian"
                            ).id,
                            "quantity": 1,
                            "unit_price": 540,
                            "intention": "For my grand-father",
                            "celebrant_id": cls.env.ref("mass.father_odilon").id,
                        },
                    )
                ],
            }
        )

    def test_donation_mass(self):
        for donation in [self.don1, self.don2, self.don3]:
            self.assertEqual(donation.state, "draft")
            donation.validate()
            self.assertEqual(donation.state, "done")
            self.assertEqual(len(donation.line_ids[0].mass_request_ids), 1)
            mass_req = donation.line_ids[0].mass_request_ids
            dline = donation.line_ids[0]
            self.assertEqual(mass_req.intention, dline.intention)
            self.assertEqual(mass_req.celebrant_id, dline.celebrant_id)
            self.assertEqual(mass_req.state, "waiting")
            self.assertEqual(mass_req.quantity, dline.quantity)
            self.assertEqual(
                mass_req.type_id.id, dline.product_id.mass_request_type_id.id
            )
            self.assertEqual(mass_req.offering, dline.amount)
            self.assertEqual(mass_req.partner_id.id, donation.partner_id.id)
            self.assertEqual(mass_req.donation_date, donation.donation_date)
            if dline.product_id == self.env.ref("mass.product_product_mass_novena"):
                self.assertEqual(mass_req.mass_quantity, 9 * dline.quantity)
            elif dline.product_id == self.env.ref(
                "mass.product_product_mass_gregorian"
            ):
                self.assertEqual(mass_req.mass_quantity, 30 * dline.quantity)
            elif dline.product_id == self.env.ref("mass.product_product_mass_simple"):
                self.assertEqual(mass_req.mass_quantity, 1 * dline.quantity)
            self.assertEqual(mass_req.mass_quantity, mass_req.mass_remaining_quantity)
