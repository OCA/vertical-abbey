# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SwapCelebrant(models.TransientModel):
    _name = 'swap.celebrant'
    _description = "Swap Celebrant"

    @api.model
    def _check_good(self):
        line_ids = self._context['active_ids']
        if len(line_ids) != 2:
            raise UserError(_(
                'You should only select 2 mass lines (%d were selected).')
                % len(line_ids))
        lines = self.env['mass.line'].browse(line_ids)
        if lines[0].date != lines[1].date:
            raise UserError(_(
                'The 2 mass lines that you selected have different dates '
                '(%s and %s). You can swap celebrants only between 2 '
                'masses of the same date.') % (lines[0].date, lines[1].date))
        return True

    pass_in_default_get = fields.Boolean(string='No', default=_check_good)
    # This field is here just to execute a default function
    # It is not visible in the view

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
