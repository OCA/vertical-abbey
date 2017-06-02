# -*- coding: utf-8 -*-
# © 2017 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestDonationMass(TransactionCase):

    def test_donation_mass(self):
        ddo = self.env['donation.donation']
        donations = ddo
        for i in range(3):
            donations += self.env.ref(
                'donation_mass.donation_mass%d' % (i + 1))
        donations.validate()
        for donation in donations:
            self.assertEquals(len(donation.line_ids[0].mass_request_ids), 1)
            mass_req = donation.line_ids[0].mass_request_ids
            dline = donation.line_ids[0]
            self.assertEquals(mass_req.intention, dline.intention)
            self.assertEquals(mass_req.celebrant_id, dline.celebrant_id)
            self.assertEquals(mass_req.state, 'waiting')
            self.assertEquals(mass_req.quantity, dline.quantity)
            self.assertEquals(
                mass_req.type_id.id, dline.product_id.mass_request_type_id.id)
            self.assertEquals(mass_req.offering, dline.amount)
            self.assertEquals(mass_req.partner_id.id, donation.partner_id.id)
            self.assertEquals(mass_req.donation_date, donation.donation_date)
            if (
                    dline.product_id ==
                    self.env.ref('mass.product_product_mass_novena')):
                self.assertEquals(mass_req.mass_quantity, 9 * dline.quantity)
            elif (
                    dline.product_id ==
                    self.env.ref('mass.product_product_mass_gregorian')):
                self.assertEquals(mass_req.mass_quantity, 30 * dline.quantity)
            elif (
                    dline.product_id ==
                    self.env.ref('mass.product_product_mass_simple')):
                self.assertEquals(mass_req.mass_quantity, 1 * dline.quantity)
            self.assertEquals(
                mass_req.mass_quantity, mass_req.mass_remaining_quantity)
