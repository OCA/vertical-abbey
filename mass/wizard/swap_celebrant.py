# -*- encoding: utf-8 -*-
##############################################################################
#
#    Mass module for OpenERP
#    Copyright (C) 2014 Artisanat Monastique de Provence
#                  (http://www.barroux.org)
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
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


class swap_celebrant(orm.TransientModel):
    _name = 'swap.celebrant'
    _description = "Swap Celebrant"

    _columns = {
        'pass_in_default_get': fields.boolean('No'),
        # This field is here just to pass in default_get()
        # It is not visible in the view
        }

    def default_get(self, cr, uid, fields_list, context=None):
        line_ids = context['active_ids']
        if len(line_ids) != 2:
            raise orm.except_orm(
                _('Error:'),
                _('You should only select 2 mass lines (%d were selected).')
                % len(line_ids))
        lines = self.pool['mass.line'].browse(
            cr, uid, line_ids, context=context)
        if lines[0].date != lines[1].date:
            raise orm.except_orm(
                _('Error:'),
                _('The 2 mass lines that you selected have different dates '
                    '(%s and %s). You can swap celebrants only between 2 '
                    'masses of the same date.')
                % (lines[0].date, lines[1].date))
        return {}

    def swap_celebrant(self, cr, uid, ids, context=None):
        line_ids = context['active_ids']
        assert len(line_ids) == 2, "Must have 2 mass IDs"
        assert context['active_model'] == 'mass.line', \
            'active_model should be mass.line'
        lines = self.pool['mass.line'].browse(
            cr, uid, line_ids, context=context)
        swapped = {
            line_ids[0]: lines[1].celebrant_id.id,
            line_ids[1]: lines[0].celebrant_id.id,
            }
        for line_id, celebrant_id in swapped.iteritems():
            self.pool['mass.line'].write(
                cr, uid, line_id, {'celebrant_id': celebrant_id},
                context=context)
        return True
