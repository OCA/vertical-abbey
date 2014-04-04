# -*- encoding: utf-8 -*-
##############################################################################
#
#    Mass module for OpenERP
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
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class res_partner(orm.Model):
    _inherit = "res.partner"

    _columns = {
        'celebrant': fields.boolean('Celebrant'),
        # A celebrant to which we give up mass is celebrant + supplier
        }


class mass_request_type(orm.Model):
    _name = "mass.request.type"
    _description = 'Types of Mass Requests'
    _order = 'name'

    _columns = {
        'name': fields.char('Mass Request Type', size=128, required=True),
        'code': fields.char('Mass Request Code', size=5),
        'quantity': fields.integer('Quantity'),
        'uninterrupted': fields.boolean('Uninterrupted'),
        # True for Neuvena and Gregorian series ; False for others
    }


class product_template(orm.Model):
    _inherit = "product.template"

    _columns = {
        'mass': fields.boolean('Mass'),
        'mass_request_type_id': fields.many2one(
            'mass.request.type', 'Mass Request Type'),
        }


class product_product(orm.Model):
    _inherit = 'product.product'

    def mass_change(self, cr, uid, ids, mass, context=None):
        res = {}
        if mass:
            res['value'] = {'type': 'service', 'sale_ok': False}
        return res


class mass_request(orm.Model):
    _name = 'mass.request'
    _description = 'Mass Request'

    def _compute_request_properties(
            self, cr, uid, ids, name, arg, context=None):
        res = {}
        for request in self.browse(cr, uid, ids, context=context):
            total_qty = request.type_id.quantity * request.quantity
            remaining_qty = total_qty
            for line in request.line_ids:
                remaining_qty -= 1
            res[request.id] = {
                'mass_remaining_quantity': remaining_qty,
                'mass_quantity': total_qty,
                }
        return res

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for request in self.browse(cr, uid, ids, context=context):
            res.append(
                (request.id,
                u'[%dx%s] %s' % (
                    request.quantity,
                    request.type_id.code,
                    request.donator_id.name)))
        return res

    _columns = {
        'donator_id': fields.many2one('res.partner', 'Donator', required=True),
        'celebrant_id': fields.many2one(
            'res.partner', 'Celebrant', domain=[('celebrant', '=', True)]),
        'donation_date': fields.date('Donation Date', required=True),
        'request_date': fields.date('Mass Request Date'),
        'type_id': fields.many2one(
            'mass.request.type', 'Mass Request Type', required=True),
        'uninterrupted': fields.related(
            'type_id', 'uninterrupted', type="boolean",
            string="Uninterrupted"),
        'offering': fields.float(
            'Offering', digits_compute=dp.get_precision('Account'),
            help="The offering amount is in company currency."),
        #'unit_offering': fields.function(
        #    _compute_unit_offering, type="float",
        #    string='Offering per Mass',
        #    digits_compute=dp.get_precision('Account'),
        #    help="This field is the offering amount of per mass is in "),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True),
        'quantity': fields.integer('Quantity'),
        'mass_quantity': fields.function(
            _compute_request_properties, type="integer",
            string="Total Mass Quantity", multi='mass_req',
            store={
                'mass.request': (
                    lambda self, cr, uid, ids, c={}:
                    ids, ['quantity', 'type_id'], 10)
            }),
        'intention': fields.char('Intention', size=256),
        'line_ids': fields.one2many(
            'mass.line', 'request_id', 'Mass Lines'),
        'state': fields.selection([
            ('waiting', 'Waiting'),
            ('started', 'Started'),
            ('transfered', 'Transfered'),
            ('done', 'Done'),
            ], 'State', readonly=True),
        'mass_remaining_quantity': fields.function(
            _compute_request_properties, type="integer", multi='mass_req',
            string="Mass Remaining Quantity"),
        'transfer_id': fields.many2one(
            'mass.request.transfer', 'Transfer Operation'),
        }

# TODO : readonly sauf en waiting
    _defaults = {
        'state': 'waiting',
        }


class mass_line(orm.Model):
    _name = 'mass.line'
    _description = 'Mass Lines'
    _order = 'date desc'

    _columns = {
        'request_id': fields.many2one('mass.request', 'Mass Request'),
        'date': fields.date('Celebration Date', required=True),
        'donator_id': fields.related(
            'request_id', 'donator_id', string="Donator", readonly=True,
            type="many2one", relation="mass.request"),
        'intention': fields.related(
            'request_id', 'intention', type="char", string="Intention",
            readonly=True),
        'request_date': fields.related(
            'request_id', 'request_date', type="date",
            string="Mass Request Date", readonly=True),
        'type_id': fields.related(
            'request_id', 'type_id', type="many2one",
            relation="mass.request.type", string="Mass Request Type",
            readonly=True),
        'unit_offering': fields.float(
            'Offering', digits_compute=dp.get_precision('Account'),
            help="The offering amount is in company currency."),
        'celebrant_id': fields.many2one(
            'res.partner', 'Celebrant', required=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True),
        }

    _defaults = {
        'state': 'draft',
        }

    def validate_mass_line(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            line.write({'state': 'done'}, context=context)
            if not line.request_id.mass_remaining_quantity:
                line.request_id.write({'state': 'done'}, context=context)
            # créer écriture comptable
        return

class mass_request_transfer(orm.Model):
    _name = 'mass.request.transfer'
    _description = 'Transfered Mass Requests'

    def _compute_transfer_totals(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for transfer in self.browse(cr, uid, ids, context=context):
            res[transfer.id] = {
                'amount_total': 0.0,
                'mass_total': 0,
                }
            for request in transfer.mass_request_ids:
                res[transfer.id]['amount_total'] += request.offering
                res[transfer.id]['mass_total'] += request.mass_quantity
        return res


    _columns = {
        'celebrant_id': fields.many2one(
            'res.partner', 'Celebrant', required=True,
            domain=[('celebrant', '=', True), ('supplier', '=', True)]),
        'transfer_date': fields.date('Transfer Date', required=True),
        'mass_request_ids': fields.one2many(
            'mass.request', 'transfer_id', 'Mass Requests'),
        'move_id': fields.many2one('account.move', 'Account Move'),
        'amount_total': fields.function(
            _compute_transfer_totals, type="float", string="Amount Total",
            digits_compute=dp.get_precision('Account'), multi="transfer"),
        'mass_total': fields.function(
            _compute_transfer_totals, type="integer",
            string="Total Mass Quantity", multi="transfer"),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True),
        }

    _defaults = {
        'transfer_date': fields.date.context_today,
        }
