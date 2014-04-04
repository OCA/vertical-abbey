# -*- encoding: utf-8 -*-
##############################################################################
#
#    Donation Stay module for OpenERP
#    Copyright (C) 2014 Artisanat Monastique de Provence (http://www.barroux.org)
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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class donation_stay_create(orm.TransientModel):
    _name = 'donation.stay.create'
    _description = 'Create Donation from a Stay'

    _columns = {
        'journal_id': fields.many2one(
            'account.journal', 'Payment Method', required=True,
            domain=[('type', '=', 'donation')]),
        'amount': fields.float(
            'Donation Amount', digits_compute=dp.get_precision('Account')),
        'date_donation': fields.date('Donation Date', required=True),
        }

    _defaults = {
        'date_donation': fields.date.context_today, #default date: today
        }

# 1. create object "donation.donation" (in database !), parameters are initialized in a "prepare function"
#(only values which need values by default)

    def _prepare_donation(self, cr, uid, stay, wizard, context=None):
        
        campaign_model, campaign_id = \
            self.pool['ir.model.data'].get_object_reference(
                cr, uid, 'donation_stay', 'stay_campaign')
        assert campaign_model == 'donation.campaign'

        # here we obtain in a tupple (model,res_id) values memorized in the table "ir.model.data" ( stay origin: xml object)
        
        product_model, stay_donation_product_id = \
            self.pool['ir.model.data'].get_object_reference(
                cr, uid, 'donation_stay', 'product_product_stay_donation') #nom du module et nom objet xml en arguments
        # "product_product_stay_donation": it's xml name for object "product_data"
        
        assert product_model == 'product.product', 'Wrong model'    # check model, assign default value
        
        product=self.pool['product.product'].browse(cr, uid, stay_donation_product_id, context=context)
        
        vals = {
          
            'partner_id': stay.partner_id.id,
            'tax_receipt_option':stay.partner_id.tax_receipt_option,
            'journal_id': wizard.journal_id.id,
            'check_total': wizard.amount,
            'donation_date': wizard.date_donation,
            'donation_campaign_id': campaign_id,
            'line_ids': [(0, 0,{ 
                        'product_id':stay_donation_product_id,
                        'amount': wizard.amount,
                        'tax_receipt_ok':product.tax_receipt_ok,
                        })],

        
        }
        return vals
    
    
    def create_donation(self, cr, uid, ids, context=None):
        print "ids=", ids
        assert len(ids) == 1, 'Only 1 ID for this wizard fonction'
        wizard = self.browse(cr, uid, ids[0], context=context)
        stay_id = context['active_id']
        stay = self.pool['stay.stay'].browse(cr, uid, stay_id, context=context)

        if not stay.partner_id:
            raise orm.except_orm(
                    _('Error:'),
                    _("This Partner is anonymous. You must create a real Partner.")
                                )

# 1. create object "donation.donation" (in database !), parameters are initialized in a "prepare fonction"
#(only values which need values by default), values stocked in "receipt_vals"
# create function used one time, but two objects are created : donation object and donation_line object
       
        donation_vals = self._prepare_donation(cr, uid, stay, wizard, context=context)
        id_donation = self.pool['donation.donation'].create(cr, uid, donation_vals, context=context)
        
        #------------------------------------------------------------
        #action_model, donation_action_id = \
        #    self.pool['ir.model.data'].get_object_reference(
        #        cr, uid, 'donation', 'donation_action')
        #assert action_model == 'ir.actions.act_window', 'Wrong action model'
        #action = self.pool[action_model].read(cr, uid, donation_action_id, context=context)
        #action.update({
        #        'nodestroy': False,
        #        'res_id': id_donation,
        #        'view_mode': 'form,tree',
        #        c)
        #------------------------------------------------------------
        
        # launch an action in order to open a view type "form" (donation form)
        
        action = {
            'name': 'Donations',
            'type': 'ir.actions.act_window',
            'res_model': 'donation.donation',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'nodestroy': False,
            'target': 'current',
            'res_id': id_donation,
            'context': context,
            
                  }
        return action
