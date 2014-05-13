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


class mass_journal_generate(orm.TransientModel):
    _name = 'mass.journal.generate'
    _description = "Generate Masses Journal"

    _columns = {
        'journal_date': fields.date('Journal Date', required=True),
        'celebrant_ids': fields.many2many(
            'res.partner', id1='partner_id', id2='wizard_id',
            string="List of celebrants"),
        }

    def _multi_allowed_dates(self, cr, uid, context):
        '''We return only Christmas date'''
        return [datetime(datetime.today().year, 12, 25)]

    def journal_date_on_change(self, cr, uid, ids, journal_date, context=None):
        line_id = self.pool['mass.line'].search(
            cr, uid, [('date', '=', journal_date)],
            limit=1, order='date desc', context=context)
        res = {'warning': {}}
        if line_id:
            journal_date_dt = datetime.strptime(
                journal_date, DEFAULT_SERVER_DATE_FORMAT)
            multi_allowed_dates = self._multi_allowed_dates(
                cr, uid, context=context)
            if journal_date_dt in multi_allowed_dates:
                res['warning'] = {
                    'title': _('Warning'),
                    'message': _('You are about to generate another journal '
                        'for %s, but it allowed for that date.')
                        % journal_date
                    }
            else:
                raise orm.except_orm(
                    _('Error:'),
                    _('There is already a journal for %s. You cannot generate '
                        'another journal for that date. OpenERP has reverted '
                        'to the default date') % journal_date)
        return res

    def _get_default_journal_date(self, cr, uid, context=None):
        line_id = self.pool['mass.line'].search(
            cr, uid, [], limit=1, order='date desc', context=context)
        res = self.pool['mass.line'].browse(cr, uid, line_id, context=context)
        if res:
            default_dt = datetime.strptime(
                res[0].date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=1)
        else:
            today_dt = datetime.today()
            default_dt = today_dt + relativedelta(days=1)
        default_str = default_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return default_str

    def _all_celebrant_ids(self, cr, uid, context=None):
        all_celebrant_ids = self.pool['res.partner'].search(
            cr, uid,
            [('celebrant', '=', True), ('supplier', '=', False)],
            context=context)
        return all_celebrant_ids

    _defaults = {
        'journal_date': _get_default_journal_date,
        'celebrant_ids': _all_celebrant_ids,
        }

    def generate_journal(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Only 1 ID in this wizard'
        if context is None:
            context = {}
        wiz = self.read(cr, uid, ids[0], context=context)
        celebrant_ids = wiz['celebrant_ids']
        
        journal_date = wiz['journal_date']
        first_journal = True
        if self.pool['mass.line'].search(
                cr, uid, [('date', '=', journal_date)], limit=1,
                order='date desc', context=context):
            first_journal = False
        if not celebrant_ids:
            raise orm.except_orm(
                _('Error:'),
                _('No celebrants were selected !'))
        number_of_celebrants = len(celebrant_ids)
        number_of_masses = 0
        mass_lines = []
        # Retreive mass requests
        # First, requests with request date = journal date and state = started
        if first_journal:
            domain1 = ['|', ('request_date', '=', journal_date), ('state', '=', 'started')]
        else:
            domain1 = [('request_date', '=', journal_date), ('uninterrupted', '=', False)]
        request_ids = self.pool['mass.request'].search(
            cr, uid, domain1, order='request_date, donation_date',
            context=context)
        for request in self.pool['mass.request'].browse(
                cr, uid, request_ids, context=context):
            if request.uninterrupted or request.celebrant_id:
                iter = 1
            else:
                iter = request.mass_remaining_quantity
            for i in range(0, iter):
                mass_lines.append({
                    'request': request,
                    'request_id': request.id,
                    'celebrant_id': request.celebrant_id.id,
                    'date': journal_date,
                    'unit_offering': request.unit_offering,
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
            if first_journal:
                domain2 = [
                    ('state', '=', 'waiting'),
                    ('request_date', '=', False),
                    ]
            else:
                domain2 = [
                    ('state', '=', 'waiting'),
                    ('request_date', '=', False),
                    ('uninterrupted', '=', False),
                    ]
            request_ids = self.pool['mass.request'].search(
                cr, uid, domain2, order='donation_date', context=context)
            for request in self.pool['mass.request'].browse(
                    cr, uid, request_ids, context=context):
                if request.uninterrupted or request.celebrant_id:
                    iter = 1
                else:
                    iter = request.mass_remaining_quantity
                for i in range(0, iter):
                    mass_lines.append({
                        'request': request,
                        'request_id': request.id,
                        'celebrant_id': request.celebrant_id.id,
                        'date': journal_date,
                        'unit_offering': request.unit_offering,
                        })
                    rest -= 1
                    if rest == 0:
                        break
                if rest == 0:
                    break

        # Record journal
        # Assign a celebrant for each mass
        print "***** Liste des célébrants = ", celebrant_ids
        celebrant_ids_origin = list(celebrant_ids)
        for line in mass_lines:
            celebrant_id = line['celebrant_id']
            if celebrant_id:
                if celebrant_id in celebrant_ids:
                    celebrant_ids.remove(celebrant_id)         
                elif celebrant_id not in celebrant_ids_origin:
                        print "***** Célébrant = ", request.celebrant_id
                        raise orm.except_orm(
                           _('Error:'),
                            _('The celebrant %s has an assigned mass for %s, but he is '
                              'not available today.')
                            % (line['request'].celebrant_id.name, line['request'].donor_id.name)                         
                            )
                else:
                    raise orm.except_orm(
                        _('Error:'),
                        _('More than one mass are assigned '
                          'to the same celebrant %s. Please, modify requests.')
                        % line['request'].celebrant_id.name
                        ) 
            else:
                celebrant_id = celebrant_ids[0]
                line['celebrant_id'] = celebrant_id
                celebrant_ids.remove(celebrant_id)
        print "***** Reste célébrants = ", wiz['celebrant_ids']
        # Create mass lines
        new_line_ids = []
        for line in mass_lines:
            line.pop('request')
            new_line_id = self.pool['mass.line'].create(
                cr, uid, line, context=context)
            new_line_ids.append(new_line_id)
        print "new_line_ids=", new_line_ids

        action = {
            'name': _('Mass Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'mass.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', new_line_ids)],
            'nodestroy': False,
            'target': 'current',
            'context': {'mass_line_main_view': True},
            }
        print "action=", action
        return action
