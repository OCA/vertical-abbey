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


class stay_journal_print(orm.TransientModel):
    _name = 'stay.journal.print'
    _description = 'Print the Stay Lines'

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

    def print_journal(self, cr, uid, ids, context=None):
        date = self.browse(cr, uid, ids[0], context=context).date
        line_ids = self.pool['stay.line'].search(
            cr, uid, [('date', '=', date)], context=context)
        if not line_ids:
            raise orm.except_orm(
                _('Error:'),
                _('No record for this date.'))
        datas = {
            'model': 'stay.line',
            'ids': line_ids,
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'stay.journal.webkit',
            'datas': datas,
            'context': context,
        }
