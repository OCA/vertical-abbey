# -*- coding: utf-8 -*-
# © 2017 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
import time


class TestGenerateMassJournal(TransactionCase):

    def test_generate_mass_journal(self):
        today = time.strftime('%Y-%m-%d')
        wiz_gen = self.env['mass.journal.generate'].create(
            {'journal_date': today})
        action_gen = wiz_gen.generate_journal()
        mass_line_ids = action_gen['domain'][0][2]
        self.assertTrue(mass_line_ids)
        mass_lines = self.env['mass.line'].browse(mass_line_ids)
        for mass_line in mass_lines:
            self.assertEquals(mass_line.date, today)
            self.assertEquals(mass_line.state, 'draft')
        wiz_val = self.env['mass.journal.validate'].create(
            {'journal_date': today})
        action_val = wiz_val.validate_journal()
        val_mass_line_ids = action_val['domain'][0][2]
        val_mass_line_ids.sort()
        mass_line_ids.sort()
        self.assertEquals(val_mass_line_ids, mass_line_ids)
        for mass_line in mass_lines:
            self.assertEquals(mass_line.state, 'done')
