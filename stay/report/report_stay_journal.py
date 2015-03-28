# -*- encoding: utf-8 -*-
##############################################################################
#
#    Stay module for Odoo
#    Copyright (C) 2014-2015 Barroux Abbey (www.barroux.org)
#    Copyright (C) 2014-2015 Akretion France (www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp.report import report_sxw
from openerp.osv import orm


class stay_journal(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(stay_journal, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'report_by_refectory': self._get_report_by_refectory,
        })

    def _get_report_by_refectory(self, date):
        user = self.pool['res.users'].browse(
            self.cr, self.uid, self.uid)
        line_ids = self.pool['stay.line'].search(
            self.cr, self.uid, [
                ('date', '=', date),
                ('company_id', '=', user.company_id.id),
                ])
        res = {}
        # {refectory_obj1 : {
        #       'lunch_subtotal': 2,
        #       'dinner_subtotal': 4,
        #       'bed_night_subtotal': 5,
        #       'lines': [line1, line2, line3],
        #       }
        # }
        for line in self.pool['stay.line'].browse(self.cr, self.uid, line_ids):
            refectory = line.refectory_id
            if refectory in res:
                res[refectory]['lunch_subtotal'] += line.lunch_qty
                res[refectory]['dinner_subtotal'] += line.dinner_qty
                res[refectory]['bed_night_subtotal']\
                    += line.bed_night_qty
                res[refectory]['lines'].append(line)
            else:
                res[refectory] = {
                    'lunch_subtotal': line.lunch_qty,
                    'dinner_subtotal': line.dinner_qty,
                    'bed_night_subtotal': line.bed_night_qty,
                    'lines': [line],
                }
        # print "res=", res
        return res.items()


class report_stay_journal(orm.AbstractModel):
    _name = 'report.stay.report_stay_journal'
    _inherit = 'report.abstract_report'
    _template = 'stay.report_stay_journal'
    _wrapped_report_class = stay_journal
