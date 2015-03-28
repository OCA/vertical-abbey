# -*- encoding: utf-8 -*-
##############################################################################
#
#    Mass module for Odoo
#    Copyright (C) 2014-2015 Barroux Abbey (www.barroux.org)
#    Copyright (C) 2014-2015 Akretion France (www.akretion.com)
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class SwapCelebrant(models.TransientModel):
    _name = 'swap.celebrant'
    _description = "Swap Celebrant"

    @api.model
    def _check_good(self):
        line_ids = self._context['active_ids']
        if len(line_ids) != 2:
            raise Warning(
                _('You should only select 2 mass lines (%d were selected).')
                % len(line_ids))
        lines = self.env['mass.line'].browse(line_ids)
        if lines[0].date != lines[1].date:
            raise Warning(
                _('The 2 mass lines that you selected have different dates '
                    '(%s and %s). You can swap celebrants only between 2 '
                    'masses of the same date.')
                % (lines[0].date, lines[1].date))
        return True

    pass_in_default_get = fields.Boolean(string='No', default=_check_good)
    # This field is here just to execute a default function
    # It is not visible in the view

    @api.multi
    def swap_celebrant(self):
        self.ensure_one()
        line_ids = self._context['active_ids']
        assert len(line_ids) == 2, "Must have 2 mass IDs"
        assert self._context['active_model'] == 'mass.line', \
            'active_model should be mass.line'
        lines = self.env['mass.line'].browse(line_ids)
        swapped = {
            lines[0]: lines[1].celebrant_id,
            lines[1]: lines[0].celebrant_id,
            }
        for line, celebrant in swapped.iteritems():
            line.celebrant_id = celebrant.id
        return
