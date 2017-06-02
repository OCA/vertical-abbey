# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests.common import TransactionCase
import time


class TestGenerateJournal(TransactionCase):

    def test_generate_journal(self):
        date = time.strftime('%Y-%m-01')
        slo = self.env['stay.line']
        # generate journal
        wiz = self.env['stay.journal.generate'].create({'date': date})
        wiz.generate()
        stay1 = self.env.ref('stay.stay1')
        stay1_line = slo.search([
            ('stay_id', '=', stay1.id), ('date', '=', date)], limit=1)
        self.assertEquals(stay1_line.date, date)
        self.assertEquals(stay1_line.partner_name, stay1.partner_name)
        self.assertFalse(stay1_line.partner_id)
        self.assertFalse(stay1_line.lunch_qty)
        self.assertEquals(stay1_line.dinner_qty, 1)
        self.assertEquals(stay1_line.bed_night_qty, 1)
        self.assertEquals(stay1_line.room_id, stay1.room_id)
        self.assertEquals(
            stay1_line.refectory_id, stay1.company_id.default_refectory_id)

        stay2 = self.env.ref('stay.stay2')
        stay2_line = slo.search([
            ('stay_id', '=', stay2.id), ('date', '=', date)], limit=1)
        self.assertEquals(stay2_line.date, date)
        self.assertEquals(stay2_line.partner_name, stay2.partner_name)
        self.assertEquals(
            stay2_line.partner_id, self.env.ref('base.res_partner_address_2'))
        self.assertEquals(stay2_line.lunch_qty, 1)
        self.assertEquals(stay2_line.dinner_qty, 1)
        self.assertEquals(stay2_line.bed_night_qty, 1)
        self.assertEquals(stay2_line.room_id, stay2.room_id)
        self.assertEquals(
            stay2_line.refectory_id, stay2.company_id.default_refectory_id)

        stay4 = self.env.ref('stay.stay4')
        stay4_line = slo.search([
            ('stay_id', '=', stay4.id), ('date', '=', date)], limit=1)
        self.assertEquals(stay4_line.date, date)
        self.assertEquals(stay4_line.partner_name, stay4.partner_name)
        self.assertFalse(stay4_line.partner_id)
        self.assertFalse(stay4_line.lunch_qty)
        self.assertFalse(stay4_line.dinner_qty)
        self.assertEquals(stay4_line.bed_night_qty, stay4.guest_qty)
        self.assertEquals(stay4_line.room_id, stay4.room_id)
        self.assertFalse(stay4_line.refectory_id)
