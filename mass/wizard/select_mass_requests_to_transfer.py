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


class mass_requests_to_transfer(orm.TransientModel):
    _name = 'mass.requests.to.transfer'
    _description = "Select Mass Requests to Transfer"

    _columns = {
        'mass_request_ids': fields.many2many(
            'mass.request', id1='mass_request_id', id2='wizard_id',
            string="Mass Requests to Transfer"),
        }

    def add_to_transfer(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Only 1 ID in this wizard'
        if context is None:
            context = {}
        wiz = self.read(cr, uid, ids[0], context=context)
        print "wiz=", wiz
        if wiz['mass_request_ids']:
            mass_request_transfer_id = context['active_id']
            print "mass_request_transfer_id=", mass_request_transfer_id
            self.pool['mass.request.transfer'].write(
                cr, uid, mass_request_transfer_id,
                {'mass_request_ids': [(6, 0, wiz['mass_request_ids'])]},
                context=context)
        return True
