# Copyright 2017-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tests.common import TransactionCase


class TestGenerateMassJournal(TransactionCase):
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
