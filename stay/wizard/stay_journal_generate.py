# -*- encoding: utf-8 -*-
##############################################################################
#
#    Stay module for OpenERP
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
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class stay_journal_generate(orm.TransientModel):
    _name = 'stay.journal.generate'
    _description = 'Generate the Stay Lines'

    _columns = {
        'date': fields.date('Date', required=True),
    }

    def _get_default_journal_date(self, cr, uid, context=None):
        today_dt = datetime.today()
        tomorrow_dt = today_dt + relativedelta(days=1)
        tomorrow_str = tomorrow_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return tomorrow_str

    _defaults = {
        'date': _get_default_journal_date,
        }

    def _prepare_stay_line(self, cr, uid, stay, date, context=None):
        stay_vals = {}
        eating_map = {
            'morning': {
                'arrival': {'lunch_multi': 1, 'dinner_multi': 1},
                'departure': {'lunch_multi': 0, 'dinner_multi': 0}
                },
            'afternoon': {
                'arrival': {'lunch_multi': 0, 'dinner_multi': 1},
                'departure': {'lunch_multi': 1, 'dinner_multi': 0}
                },
            'evening': {
                'arrival': {'lunch_multi': 0, 'dinner_multi': 0},
                'departure': {'lunch_multi': 1, 'dinner_multi': 1}
                },
            }

        if date == stay.arrival_date:
            stay_vals = {
                'lunch_qty':
                    stay.guest_qty *
                    eating_map[stay.arrival_time]
                    ['arrival']['lunch_multi'],
                'dinner_qty':
                    stay.guest_qty *
                    eating_map[stay.arrival_time]
                    ['arrival']['dinner_multi'],
                'bed_night_qty': stay.guest_qty,
                }
        elif date == stay.departure_date:
            if stay.departure_time == 'morning':
                return {}
            stay_vals = {
                'lunch_qty':
                    stay.guest_qty *
                    eating_map[stay.departure_time]
                    ['departure']['lunch_multi'],
                'dinner_qty':
                    stay.guest_qty *
                    eating_map[stay.departure_time]
                    ['departure']['dinner_multi'],
                'bed_night_qty': 0,
                }
        else:
            stay_vals = {
                'lunch_qty': stay.guest_qty,
                'dinner_qty': stay.guest_qty,
                'bed_night_qty': stay.guest_qty,
            }
        if not stay.company_id.default_refectory_id:
            raise orm.except_orm(
                _('Error:'),
                _("Missing default refectory on the company '%s'.")
                % stay.company_id.name)
        stay_vals.update({
            'date': date,
            'stay_id': stay.id,
            'partner_id': stay.partner_id.id,
            'partner_name': stay.partner_name,
            'refectory_id': stay.company_id.default_refectory_id.id,
            'room_id': stay.room_id.id,
            'company_id': stay.company_id.id,
        })
        return stay_vals

    def generate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        date = self.browse(cr, uid, ids[0], context=context).date
        line_ids_to_delete = self.pool['stay.line'].search(
            cr, uid,
            [('date', '=', date), ('stay_id', '!=', False)],
            context=context)
        if line_ids_to_delete:
            self.pool['stay.line'].unlink(
                cr, uid, line_ids_to_delete, context=context)
        stay_ids = self.pool['stay.stay'].search(cr, uid, [
            ('arrival_date', '<=', date),
            ('departure_date', '>=', date),
            ], context=context)
        for stay in self.pool['stay.stay'].browse(
                cr, uid, stay_ids, context=context):
            vals = self._prepare_stay_line(
                cr, uid, stay, date, context=context)
            if vals:
                self.pool['stay.line'].create(cr, uid, vals, context=context)

        action_model, action_id =\
            self.pool['ir.model.data'].get_object_reference(
                cr, uid, 'stay', 'stay_line_action')
        assert action_model == 'ir.actions.act_window', 'Wrong model'
        action = self.pool[action_model].read(
            cr, uid, action_id, context=context)
        action.update({
            'view_mode': 'tree,form',
            'domain': [('date', '=', date)],
            })
        return action

