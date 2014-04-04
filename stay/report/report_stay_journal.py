# -*- encoding: utf-8 -*-
##############################################################################
#
#    Stay module for OpenERP
#    Copyright (C) 2014 Akretion (http://www.akretion.com)
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


class stay_journal_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(stay_journal_report, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'report_by_refectory': self._get_report_by_refectory,
        })

    def _get_report_by_refectory(self, lines, context=None):
        res = {}
        # {date1: {
        #    refectory_obj1 : {
        #       'lunch_subtotal': 2,
        #        'dinner_subtotal': 4,
        #       'bed_night_subtotal': 5,
        #        'lines': [line1, line2, line3],
        #       }
        #    }
        # }
        for line in lines:
            date = line.date
            if date not in res:
                res[date] = {}
            refectory = line.refectory_id
            if refectory in res[date]:
                res[date][refectory]['lunch_subtotal'] += line.lunch_qty
                res[date][refectory]['dinner_subtotal'] += line.dinner_qty
                res[date][refectory]['bed_night_subtotal']\
                    += line.bed_night_qty
                res[date][refectory]['lines'].append(line)
            else:
                res[date][refectory] = {
                    'lunch_subtotal': line.lunch_qty,
                    'dinner_subtotal': line.dinner_qty,
                    'bed_night_subtotal': line.bed_night_qty,
                    'lines': [line],
                }
        print "res=", res
        # TODO : order by date when there are multiple dates in the report
        return res


# the 1st arg MUST be "report.%s" % name of the report !
report_sxw.report_sxw('report.stay.journal.webkit',
                      'stay.line',
                      'addons/stay/report/report_stay_journal.mako',
                      parser=stay_journal_report)
