# -*- encoding: utf-8 -*-
##############################################################################
#
#    Donation Mass module for OpenERP
#    Copyright (C) 2014 Artisanat Monastique de Provence
#                  (http://www.barroux.org)
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


class donation_line(orm.Model):
    _inherit = 'donation.line'

    def product_id_change(self, cr, uid, ids, product_id, context):
        res = super(donation_line, self).product_id_change(
            cr, uid, ids, product_id, context=context)
        if product_id:
            product = self.pool['product.product'].browse(
                cr, uid, product_id, context=context)
            res['value']['mass'] = product.mass
        return res

    _columns = {
        'mass': fields.boolean('Is a Mass'),
        'celebrant_id': fields.many2one(
            'res.partner', 'Celebrant',
            domain=[('celebrant', '=', True)]),
        'mass_request_date': fields.date('Mass Request Date'),
        'intention': fields.char('Intention', size=256),
        }


class donation_donation(orm.Model):
    _inherit = 'donation.donation'

    def _prepare_mass_request(
            self, cr, uid, donation, donation_line, context=None):
        vals = {
            'donor_id': donation.partner_id.id,
            'celebrant_id': donation_line.celebrant_id.id or False,
            'donation_date': donation.donation_date,
            'request_date': donation_line.mass_request_date or False,
            'type_id': donation_line.product_id.mass_request_type_id.id,
            'offering': donation_line.amount_company_currency,
            'stock_account_id': donation_line.product_id.property_account_income.id,
            'analytic_account_id': donation_line.analytic_account_id.id or False,
            'quantity': donation_line.quantity,
            'intention': donation_line.intention,
            'donation_line_id': donation_line.id,
            'company_id': donation.company_id.id,
        }
        return vals

    def validate(self, cr, uid, ids, context=None):
        res = super(donation_donation, self).validate(
            cr, uid, ids, context=context)
        donation = self.browse(cr, uid, ids[0], context=context)
        for line in donation.line_ids:
            if line.product_id.mass:
                vals = self._prepare_mass_request(
                    cr, uid, donation, line, context=context)
                self.pool['mass.request'].create(
                    cr, uid, vals, context=context)
        return res
