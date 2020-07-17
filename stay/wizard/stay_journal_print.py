# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# @author: Brother Irénée
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
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
    date_label = fields.Char(compute='_compute_date_label', readonly=True)

    @api.depends('date')
    def _compute_date_label(self):
        for wiz in self:
            res = self.env['stay.date.label'].search(
                [('date', '=', self.date)], limit=1)
            wiz.date_label = res and res.name or False

    def print_journal(self):
        self.ensure_one()
        lines = self.env['stay.line'].search([
            ('date', '=', self.date),
            ('company_id', '=', self.env.user.company_id.id),
            ])
        if not lines:
            raise UserError(_('No stay for this date.'))
        res = self.env['report'].get_action(
            self,
            'stay.report_stayjournalprint')
        # res['datas'] = data  # To be compatible with aeroo v8
        return res

    def get_report_by_refectory(self):
        '''Method for the report (replace report parser)'''
        lines = self.env['stay.line'].search([
            ('date', '=', self.date),
            ('company_id', '=', self.env.user.company_id.id),
            ])
        res = {}
        # {refectory_obj1 : {
        #       'lunch_subtotal': 2,
        #       'dinner_subtotal': 4,
        #       'bed_night_subtotal': 5,
        #       'lines': [line1, line2, line3],
        #       }
        # }
        for line in lines:
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
        # print "res=", res.items()
        return res.items()
