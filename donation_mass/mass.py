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


class mass_request(orm.Model):
    _inherit = "mass.request"

    _columns = {
        'donation_line_id': fields.many2one(
            'donation.line', 'Related Donation Line', readonly=True),
        'donation_id': fields.related(
            'donation_line_id', 'donation_id', type='many2one',
            relation='donation.donation', string="Related Donation",
            readonly=True),
        }


class mass_line(orm.Model):
    _inherit = 'mass.line'

    _columns = {
        'move_id': fields.many2one(
            'account.move', 'Account Move', readonly=True),
        }
