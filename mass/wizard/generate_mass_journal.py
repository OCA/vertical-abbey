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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _


class mass_journal(orm.TransientModel):
    _name = 'mass.journal'
    _description = "Generate Masses Journal"

    _columns = {
        'journal_date': fields.date('Journal Date'),
        'celebrant_ids': fields.many2many(
            'res.partner', id1='partner_id', id2='wizard_id',
            string="List of celebrants"),
        }
    
    def _get_default_journal_date(self, cr, uid, context=None):
        request_id = self.pool['mass.line'].search(cr, uid, [], limit=1)
        res = self.pool['mass.line'].browse(cr, uid, request_id, context=context)
        if (res):
            default_dt = datetime.strptime(res[0].date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=1)
        else:
            today_dt = datetime.today()
            default_dt = today_dt + relativedelta(days=1)
        default_str = default_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return default_str

    _defaults = {
        'journal_date': _get_default_journal_date,
        }
    
    def generate_journal(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Only 1 ID in this wizard'
        if context is None:
            context = {}
        wiz = self.read(cr, uid, ids[0], context=context)
        celebrant_ids = wiz['celebrant_ids']
        journal_date = wiz['journal_date']
        default_date = _get_default_journal_date
        #TODO Verify journal_date == default_date
        # if journal_date != default_date:
            # Display a warning message
        if celebrant_ids:
            number_of_celebrants = len(celebrant_ids)
            number_of_masses = 0
            mass_lines = []
            # Retreive mass requests
            # First, requests with request date = journal date and state = started
            request_ids = self.pool['mass.request'].search(
                cr, uid,
                ['|', ('request_date', '=', journal_date), ('state', '=', 'started'),],
                order='request_date,donation_date')
            for request in self.pool['mass.request'].browse(cr, uid, request_ids, context=context):
                if request.uninterrupted or request.celebrant_id:
                    iter = 1
                else:
                    iter = request.mass_remaining_quantity
                for i in range(0, iter):
                    mass_lines.append({
                        'request_id': request.id,
                        'celebrant_id': request.celebrant_id.id,
                        'date': journal_date,
                        'unit_offering': request.offering/request.mass_quantity,
                        })
            rest = number_of_celebrants - len(mass_lines)
            if rest < 0:
                raise orm.except_orm(
                    _('Error:'),
                    _('The number of requests for this day exceeds '
                        'the number of celebrants. Please, modify requests.')
                    )
            if rest > 0:             
                # Last, requests with state = waiting (fifo rule)
                request_ids = self.pool['mass.request'].search(
                    cr, uid, 
                    [('state', '=', 'waiting')], order='donation_date')
                for request in self.pool['mass.request'].browse(
                    cr, uid, request_ids, context=context):
                    if not request.request_date:
                        if request.uninterrupted or request.celebrant_id:
                            iter = 1
                        else:
                            iter = request.mass_remaining_quantity
                        for i in range(0, iter):
                            mass_lines.append({
                                'request_id': request.id,
                                'celebrant_id': request.celebrant_id.id,
                                'date': journal_date,
                                'unit_offering': request.offering/request.mass_quantity,
                                })
                            rest -= 1
                            if rest == 0:
                                break
                        if rest == 0:
                            break
                    
            # Record journal
            # Assign a celebrant for each mass
            for line in range(0, len(mass_lines)):
                celebrant_id = mass_lines[line]['celebrant_id']
                if celebrant_id:
                    if celebrant_id in celebrant_ids:
                        celebrant_ids.remove(celebrant_id)
                    else:
                        raise orm.except_orm(
                            _('Error:'),
                            _('More than one mass are assigned '
                              'to the same celebrant. Please, modify requests.')
                            ) 
                else:
                    celebrant_id = celebrant_ids[0]
                    mass_lines[line]['celebrant_id'] = celebrant_id
                    celebrant_ids.remove(celebrant_id)
            # Create mass lines
            for line in range(0, len(mass_lines)):
                self.pool['mass.line'].create(cr, uid, mass_lines[line], context=context)
        else:
            raise orm.except_orm(
                _('Error:'),
                _('No celebrants were selected !'))
    
        return
    
