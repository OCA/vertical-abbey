# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo import fields


class TestDonationFromStay(TransactionCase):

    def test_donate_from_stay(self):
        today = fields.date.context_today(self)
        dsco = self.env['donation.stay.create']
        ctx = self._context.copy()
        ctx.update({
            'active_id': self.env.ref('stay.stay2').id,
            'active_ids': [self.env.ref('stay.stay2').id],
            'active_model': 'stay.stay'})
        wiz = dsco.with_context(ctx).create({
            'journal_id': self.env.ref('account.check_journal').id,
            'amount': 200,
            'payment_ref': 'CHQ LBP 421242'})
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
        self.assertEquals(donation.move_id.date, today)
        self.assertEquals(
            donation.move_id.journal_id, self.env.ref('account.check_journal'))
        self.assertEquals(donation.move_id.ref, 'CHQ LBP 421242')
