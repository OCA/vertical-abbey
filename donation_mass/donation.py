# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DonationLine(models.Model):
    _inherit = 'donation.line'

    mass = fields.Boolean(related='product_id.mass', readonly=True, store=True)
    celebrant_id = fields.Many2one(
        'res.partner', string='Celebrant', ondelete='restrict',
        domain=[('celebrant', '=', True), ('supplier', '=', False)])
    mass_request_date = fields.Date(string='Celebration Requested Date')
    intention = fields.Char(string='Intention')
    mass_request_ids = fields.One2many(
        'mass.request', 'donation_line_id', string='Masses')


class DonationDonation(models.Model):
    _inherit = 'donation.donation'

    @api.model
    def _prepare_mass_request(self, donation_line):
        donation = donation_line.donation_id
        account_id = (
            donation_line.product_id.property_account_income_id.id or False)
        if not account_id:
            account_id = (
                donation_line.product_id.categ_id.
                property_account_income_categ_id.id or False)
        vals = {
            'partner_id': donation.partner_id.id,
            'celebrant_id': donation_line.celebrant_id.id or False,
            'donation_date': donation.donation_date,
            'request_date': donation_line.mass_request_date or False,
            'type_id': donation_line.product_id.mass_request_type_id.id,
            'offering': donation_line.amount_company_currency,
            'stock_account_id': account_id,
            'analytic_account_id':
            donation_line.analytic_account_id.id or False,
            'quantity': donation_line.quantity,
            'intention': donation_line.intention,
            'donation_line_id': donation_line.id,
            'company_id': donation.company_id.id,
        }
        return vals

    @api.one
    def validate(self):
        res = super(DonationDonation, self).validate()
        for line in self.line_ids:
            if line.product_id.mass:
                vals = self._prepare_mass_request(line)
                self.env['mass.request'].create(vals)
        return res

    @api.one
    def done2cancel(self):
        mass_requests = self.env['mass.request'].search(
            [('donation_id', '=', self.id)])
        if mass_requests:
            for mass_request in mass_requests:
                if mass_request.state != 'waiting':
                    raise UserError(_(
                        'Cannot cancel the donation with number '
                        '%s because it is linked to a mass request in '
                        '%s state.')
                        % (self.number, mass_request.state))
            self.message_post(_('%d related mass request(s) in waiting state '
                                'have been deleted.') % len(mass_requests))
            mass_requests.unlink()
        return super(DonationDonation, self).done2cancel()
