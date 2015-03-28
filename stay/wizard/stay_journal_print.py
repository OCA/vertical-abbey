# -*- encoding: utf-8 -*-
##############################################################################
#
#    Stay module for Odoo
#    Copyright (C) 2014-2015 Barroux Abbey (www.barroux.org)
#    Copyright (C) 2014-2015 Akretion France (www.akretion.com)
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    @author: Brother Bernard <informatique@barroux.org>
#    @author: Brother Irénée
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

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta


class StayJournalPrint(models.TransientModel):
    _name = 'stay.journal.print'
    _description = 'Print the Stay Lines'
    _rec_name = 'date'

    @api.model
    def _default_date(self):
        today_str = fields.Date.context_today(self)
        today_dt = fields.Date.from_string(today_str)
        return today_dt + relativedelta(days=1)

    date = fields.Date(string='Date', required=True, default=_default_date)

    @api.multi
    def print_journal(self):
        self.ensure_one()
        lines = self.env['stay.line'].search([
            ('date', '=', self.date),
            ('company_id', '=', self.env.user.company_id.id),
            ])
        if not lines:
            raise Warning(_('No stay for this date.'))
        data = {'date': self.date}
        res = self.env['report'].get_action(
            self.env['report'].browse(False), 'stay.report_stay_journal',
            data=data)
        res['datas'] = data  # To be compatible with aeroo v8
        return res
