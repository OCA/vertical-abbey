# -*- encoding: utf-8 -*-
##############################################################################
#
#    Donation Stay module for OpenERP
#    Copyright (C) 2014 Artisanat Monastique de Provence
#       (http://www.barroux.org)
#    @author: Brother Irénée
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

from openerp.osv import orm, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class donation_stay_create(orm.TransientModel):
    _name = 'donation.stay.create'
    _description = 'Create Donation from a Stay'

    _columns = {
        'journal_id': fields.many2one(
            'account.journal', 'Payment Method', required=True,
            domain=[
                ('type', 'in', ('bank', 'cash')),
                ('allow_donation', '=', True)]),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True),
        'amount': fields.float(
            'Donation Amount', digits_compute=dp.get_precision('Account')),
        'date_donation': fields.date('Donation Date', required=True),
        'payment_ref': fields.char('Payment Reference', size=32),
        }

    def _get_default_currency(self, cr, uid, context=None):
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        return user.company_id.currency_id.id

    _defaults = {
        'date_donation': fields.date.context_today,  # default date: today
        'currency_id': _get_default_currency,
        }

    # 1. create object "donation.donation" (in database !),
    # parameters are initialized in a "prepare function"
    # (only values which need values by default)
    def _prepare_donation(self, cr, uid, stay, wizard, context=None):

        campaign_model, campaign_id = \
            self.pool['ir.model.data'].get_object_reference(
                cr, uid, 'donation_stay', 'stay_campaign')
        assert campaign_model == 'donation.campaign'

        # here we obtain in a tupple (model,res_id) values memorized
        # in the table "ir.model.data" (stay origin: xml object)
        product_model, stay_donation_product_id = \
            self.pool['ir.model.data'].get_object_reference(
                cr, uid, 'donation_stay', 'product_product_stay_donation')
        # "product_product_stay_donation":
        # it's the xml name for object "product_data"

        # check model, assign default value
        assert product_model == 'product.product', 'Wrong model'

        product_change = self.pool['donation.line'].product_id_change(
            cr, uid, [], stay_donation_product_id, context=context)
        line_vals = product_change['value']
        line_vals.update({
            'product_id': stay_donation_product_id,
            'quantity': 1,
            'unit_price': wizard.amount,
            })
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        partner_change = self.pool['donation.donation'].partner_id_change(
            cr, uid, [], stay.partner_id.id, user.company_id.id,
            context=context)
        if partner_change and partner_change.get('value'):
            vals = partner_change['value']
        else:
            vals = {}
        vals.update({
            'partner_id': stay.partner_id.id,
            'journal_id': wizard.journal_id.id,
            'currency_id': wizard.currency_id.id,
            'payment_ref': wizard.payment_ref,
            'check_total': wizard.amount,
            'donation_date': wizard.date_donation,
            'campaign_id': campaign_id,
            'line_ids': [(0, 0, line_vals)],
        })
        return vals

    def create_donation(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Only 1 ID for this wizard fonction'
        wizard = self.browse(cr, uid, ids[0], context=context)
        stay_id = context['active_id']
        stay = self.pool['stay.stay'].browse(cr, uid, stay_id, context=context)

        if not stay.partner_id:
            raise orm.except_orm(
                _('Error:'),
                _("This Partner is anonymous. You must create a real "
                    "Partner."))

        # 1. create object "donation.donation" (in database !),
        # parameters are initialized in a "prepare fonction"
        # (only values which need values by default),
        # values stocked in "receipt_vals"
        # create function used one time, but two objects are created :
        # donation object and donation_line object
        donation_vals = self._prepare_donation(
            cr, uid, stay, wizard, context=context)
        donation_id = self.pool['donation.donation'].create(
            cr, uid, donation_vals, context=context)

        # launch an action in order to open a view type "form" (donation form)
        action = {
            'name': _('Donations'),
            'type': 'ir.actions.act_window',
            'res_model': 'donation.donation',
            'view_mode': 'form,tree,graph',
            'nodestroy': False,
            'target': 'current',
            'res_id': donation_id,
            'context': context,
            }
        return action
