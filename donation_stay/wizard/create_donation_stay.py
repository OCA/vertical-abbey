# -*- encoding: utf-8 -*-
##############################################################################
#
#    Donation Stay module for Odoo
#    Copyright (C) 2014-2015 Barroux Abbey (www.barroux.org)
#    Copyright (C) 2014-2015 Akretion France (www.akretion.com)
#    @author: Brother Irénée
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp


class DonationStayCreate(models.TransientModel):
    _name = 'donation.stay.create'
    _description = 'Create Donation from a Stay'
    _rec_name = 'journal_id'

    journal_id = fields.Many2one(
        'account.journal', string='Payment Method', required=True,
        domain=[
            ('type', 'in', ('bank', 'cash')),
            ('allow_donation', '=', True)])
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Float(
        string='Donation Amount', digits=dp.get_precision('Account'))
    date_donation = fields.Date(
        'Donation Date', required=True, default=fields.Date.context_today)
    payment_ref = fields.Char('Payment Reference', size=32)

    # 1. create object "donation.donation" (in database !),
    # parameters are initialized in a "prepare function"
    # (only values which need values by default)
    @api.model
    def _prepare_donation(self, stay):
        campaign = self.env.ref('donation_stay.stay_campaign')
        stay_donation_product = self.env.ref(
            'donation_stay.product_product_stay_donation')
        line_vals = {
            'product_id': stay_donation_product.id,
            'quantity': 1,
            'unit_price': self.amount,
            }
        vals = {
            'partner_id': stay.partner_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'payment_ref': self.payment_ref,
            'check_total': self.amount,
            'donation_date': self.date_donation,
            'campaign_id': campaign.id,
            'line_ids': [(0, 0, line_vals)],
            'company_id': stay.company_id.id,
        }
        return vals

    @api.multi
    def create_donation(self):
        self.ensure_one()
        assert self.env.context.get('active_model') == 'stay.stay',\
            'Underlying model should be stay.stay'
        stay = self.env['stay.stay'].browse(self.env.context['active_id'])

        if not stay.partner_id:
            raise Warning(
                _("This Partner is anonymous. You must create a real "
                    "Partner."))

        # 1. create object "donation.donation" (in database !),
        # parameters are initialized in a "prepare fonction"
        # (only values which need values by default),
        # values stocked in "receipt_vals"
        # create function used one time, but two objects are created :
        # donation object and donation_line object
        donation_vals = self._prepare_donation(stay)
        donation = self.env['donation.donation'].create(donation_vals)
        donation.partner_id_change()
        donation.line_ids.product_id_change()

        # launch an action in order to open a view type "form" (donation form)
        action = {
            'name': _('Donations'),
            'type': 'ir.actions.act_window',
            'res_model': 'donation.donation',
            'view_mode': 'form,tree,graph',
            'nodestroy': False,
            'target': 'current',
            'res_id': donation.id,
            }
        return action
