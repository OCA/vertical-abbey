# -*- encoding: utf-8 -*-
##############################################################################
#
#    Stay module for OpenERP
#    Copyright (C) 2014 Artisanat Monastique de Provence
#                       (http://www.barroux.org)
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author: Brother Bernard <informatique@barroux.org>
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
from openerp.tools.translate import _


class stay_stay(orm.Model):
    _name = 'stay.stay'
    _description = 'Guest Stay'
    _order = 'arrival_date desc'

    _columns = {
        'name': fields.char('Stay Number', size=32, readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'partner_id': fields.many2one(
            'res.partner', 'Guest',
            help="If guest is anonymous, leave this field empty."),
        'partner_name': fields.char('Guest Name', size=128, required=True),
        'guest_qty': fields.integer('Guest Quantity'),
        'arrival_date': fields.date('Arrival Date', required=True),
        'arrival_time': fields.selection([
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
            ], 'Arrival Time', required=True),
        'departure_date': fields.date('Departure Date', required=True),
        'departure_time': fields.selection([
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
            ], 'Departure Time', required=True),
        'room_id': fields.many2one('stay.room', 'Room'),
        'line_ids': fields.one2many('stay.line', 'stay_id', 'Stay Lines'),
        'note': fields.text('Notes'),
        'create_uid': fields.many2one('res.users', 'Created by'),
        }

    _defaults = {
        'guest_qty': 1,
        'company_id': lambda self, cr, uid, context:
            self.pool['res.company']._company_default_get(
                cr, uid, 'stay.stay', context=context),
        'name': '/',
        }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool['ir.sequence'].next_by_code(
                cr, uid, 'stay.stay', context=context)
        return super(stay_stay, self).create(cr, uid, vals, context=context)

    # constraint date arrival < date departure
    def _check_stay_date(self, cr, uid, ids):
        for stay in self.browse(cr, uid, ids):
            if stay.arrival_date >= stay.departure_date:
                return False
        return True

    _constraints = [(
        _check_stay_date,
        'Arrival date must be earlier than departure date',
        ['arrival_date', 'departure_date'])
        ]

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)',
         'A stay with this number already exists for this company.'),
        ]

    def partner_id_change(self, cr, uid, ids, partner_id, context=None):
        res = {'value': {'partner_name': False}}
        if partner_id:
            partner = self.pool['res.partner'].browse(
                cr, uid, partner_id, context=context)
            name = partner.name
            if partner.title and partner.title.shortcut:
                name = u'%s %s' % (partner.title.shortcut, name)
            res['value']['partner_name'] = name
        return res


class stay_refectory(orm.Model):
    _name = 'stay.refectory'
    _description = 'Refectory'

    _columns = {
        'code': fields.char('Code', size=10),
        'name': fields.char('Name', size=64, required=True),
        'capacity': fields.integer('Capacity'),
    }

    _sql_constraints = [
        ('code_uniq', 'unique(code)',
         'A refectory with this code already exists.'),
        ]


class stay_room(orm.Model):
    _name = 'stay.room'
    _description = 'room'

    _columns = {
        'code': fields.char('Code', size=10),
        'name': fields.char('Name', size=64, required=True),
        'bed_qty': fields.integer('Number of beds'),
        }

    _defaults = {
        'bed_qty': 1,
    }

    _sql_constraints = [
        ('code_uniq', 'unique(code)',
         'A room with this code already exists.'),
        ]


class stay_line(orm.Model):
    _name = 'stay.line'
    _description = 'Stay Journal'
    _rec_name = 'partner_name'
    _order = 'date desc'

    _columns = {
        'stay_id': fields.many2one('stay.stay', 'Stay'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'date': fields.date('Date', required=True),
        'lunch_qty': fields.integer('Lunches'),
        'dinner_qty': fields.integer('Dinners'),
        'bed_night_qty': fields.integer('Bed Nights'),
        'partner_id': fields.many2one(
            'res.partner', 'Guest',
            help="If guest is anonymous, leave this field empty."),
        'partner_name': fields.char('Guest Name', size=128, required=True),
        'refectory_id': fields.many2one('stay.refectory', 'Refectory'),
        'room_id': fields.many2one('stay.room', 'Room'),
        }

    def default_refectory(self, cr, uid, context=None):
        company_id = self.pool['res.company']._company_default_get(
            cr, uid, 'stay.stay', context=context)
        company = self.pool['res.company'].browse(
            cr, uid, company_id, context=context)
        refectory_id = company.default_refectory_id \
            and company.default_refectory_id.id or False
        return refectory_id

    _defaults = {
        'refectory_id': default_refectory,
        'date': fields.date.context_today,
        'company_id': lambda self, cr, uid, context:
            self.pool['res.company']._company_default_get(
                cr, uid, 'stay.line', context=context),
        }

    def _check_refectory(self, cr, uid, ids):
        for line in self.browse(cr, uid, ids):
            if (line.lunch_qty or line.dinner_qty) and not line.refectory_id:
                raise orm.except_orm(
                    _('Error:'),
                    _("Missing refectory for guest '%s' on %s.")
                    % (line.partner_name, line.date))
        return True

    _constraints = [(
        _check_refectory,
        "Error msg in raise",
        ['refectory_id', 'lunch_qty', 'dinner_qty']
    )]

    _sql_constraints = [
        ('lunch_qty_positive', 'CHECK (lunch_qty >= 0)',
            'The number of lunches must be positive or null'),
        ('dinner_qty_positive', 'CHECK (dinner_qty >= 0)',
            'The number of dinners must be positive or null'),
        ('bed_night_qty_positive', 'CHECK (bed_night_qty >= 0)',
            'The number of bed nights must be positive or null'),
    ]

    def partner_id_change(self, cr, uid, ids, partner_id, context=None):
        return self.pool['stay.stay'].partner_id_change(
            cr, uid, [], partner_id, context=context)
