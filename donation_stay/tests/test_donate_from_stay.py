# -*- coding: utf-8 -*-
# Copyright 2017-2019 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestDonationFromStay(TransactionCase):

    def test_donate_from_stay(self):
        dsco = self.env['donation.stay.create']
        ctx = {
            'active_id': self.env.ref('stay.stay2').id,
            'active_ids': [self.env.ref('stay.stay2').id],
            'active_model': 'stay.stay'}
        bq_journal = self.env['account.journal'].search(
            [('type', '=', 'bank')])
        payment_ref = 'CHQ LBP 421242'
        wiz = dsco.with_context(ctx).create({
            'journal_id': bq_journal[0].id,
            'amount': 200,
            'payment_ref': payment_ref})
        action = wiz.create_donation()
        donation_id = action['res_id']
        donation = self.env['donation.donation'].browse(donation_id)
        self.assertEquals(donation.state, 'draft')
        self.assertEquals(donation.campaign_id, self.env.ref('stay_campaign'))
        self.assertEquals(donation.amount_total, 200)
        donation.validate()
        self.assertEquals(
            donation.partner_id, self.env.ref('base.res_partner_address_2'))
        self.assertEquals(donation.move_id.state, 'posted')
        self.assertEquals(
            donation.move_id.journal_id, bq_journal[0])
        self.assertEquals(donation.move_id.ref, payment_ref)
