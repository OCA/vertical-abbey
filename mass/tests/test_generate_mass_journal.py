# Copyright 2017-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime

from odoo.tests.common import TransactionCase


class TestGenerateMassJournal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.journal = cls.env["account.journal"].create(
            {
                "type": "general",
                "code": "ZMASS",
                "name": "Mass Validation",
                "company_id": cls.company.id,
            }
        )
        cls.stock_account = cls.env["account.account"].create(
            {
                "code": "MASSTOCK",
                "name": "Mass Stock test",
                "company_id": cls.company.id,
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        cls.company.write(
            {
                "mass_validation_journal_id": cls.journal.id,
                "mass_stock_account_id": cls.stock_account.id,
            }
        )
        cls.massreq1 = cls.env["mass.request"].create(
            {
                "partner_id": cls.env.ref("mass.partner1").id,
                "donation_date": time.strftime("%Y-%m-%d"),
                "product_id": cls.env.ref("mass.product_product_mass_simple").id,
                "offering": 17.0,
                "company_id": cls.company.id,
                "quantity": 1,
                "intention": "for my childrens",
            }
        )
        cls.massreq2 = cls.env["mass.request"].create(
            {
                "partner_id": cls.env.ref("mass.partner2").id,
                "donation_date": time.strftime("%Y-%m-%d"),
                "product_id": cls.env.ref("mass.product_product_mass_novena").id,
                "offering": 170.0,
                "company_id": cls.company.id,
                "quantity": 1,
                "intention": "for my Grand-Father",
            }
        )
        cls.massreq3 = cls.env["mass.request"].create(
            {
                "partner_id": cls.env.ref("mass.partner3").id,
                "donation_date": time.strftime("%Y-%m-%d"),
                "product_id": cls.env.ref("mass.product_product_mass_gregorian").id,
                "offering": 540.0,
                "company_id": cls.company.id,
                "quantity": 1,
                "intention": "for my grand-mother",
            }
        )
        cls.massreq4 = cls.env["mass.request"].create(
            {
                "partner_id": cls.env.ref("mass.partner4").id,
                "donation_date": time.strftime("%Y-%m-%d"),
                "product_id": cls.env.ref("mass.product_product_mass_simple").id,
                "offering": 51.0,
                "company_id": cls.company.id,
                "quantity": 3,
                "intention": "for my success at my exams",
            }
        )

    def test_generate_mass_journal(self):
        today = datetime.now().date()
        wiz_gen = self.env["mass.journal.generate"].create({"journal_date": today})
        action_gen = wiz_gen.generate_journal()
        mass_line_ids = action_gen["domain"][0][2]
        self.assertTrue(mass_line_ids)
        mass_lines = self.env["mass.line"].browse(mass_line_ids)
        for mass_line in mass_lines:
            self.assertEqual(mass_line.date, today)
            self.assertEqual(mass_line.state, "draft")
        wiz_val = self.env["mass.journal.validate"].create({"journal_date": today})
        action_val = wiz_val.validate_journal()
        val_mass_line_ids = action_val["domain"][0][2]
        val_mass_line_ids.sort()
        mass_line_ids.sort()
        self.assertEqual(val_mass_line_ids, mass_line_ids)
        for mass_line in mass_lines:
            self.assertEqual(mass_line.state, "done")
            self.assertTrue(mass_line.move_id)
            self.assertEqual(mass_line.move_id.date, mass_line.date)
            self.assertEqual(
                mass_line.move_id.journal_id,
                mass_line.company_id.mass_validation_journal_id,
            )
