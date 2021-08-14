# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class StayJournalGenerate(models.TransientModel):
    _name = 'stay.journal.generate'
    _description = 'Generate the Stay Lines'
    _rec_name = 'date'

    @api.model
    def _default_date(self):
        today_dt = fields.Date.context_today(self)
        tomorrow_dt = today_dt + relativedelta(days=1)
        return tomorrow_dt

    date = fields.Date(
        string='Date', required=True, default=lambda self: self._default_date())
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)

    def _prepare_stay_line(self, stay):
        vals = {
            'date': self.date,
            'stay_id': stay.id,
            'partner_id': stay.partner_id.id,
            'partner_name': stay.partner_name,
            'refectory_id': stay.company_id.default_refectory_id.id,
            'room_id': stay.room_id.id,
            'company_id': stay.company_id.id,
            'lunch_qty': 0,
            'dinner_qty': 0,
            'bed_night_qty': 0,
            }
        if self.date == stay.arrival_date and self.date == stay.departure_date:
            if stay.arrival_time == 'morning':
                # then departure_time is afternoon or evening
                vals['lunch_qty'] = stay.guest_qty
                if stay.departure_time == 'evening':
                    vals['dinner_qty'] = stay.guest_qty
            elif stay.arrival_time == 'afternoon':
                # then departure_time is evening
                vals['dinner_qty'] = stay.guest_qty
        elif self.date == stay.arrival_date:
            vals['bed_night_qty'] = stay.guest_qty
            if stay.arrival_time == 'morning':
                vals['lunch_qty'] = stay.guest_qty
                vals['dinner_qty'] = stay.guest_qty
            elif stay.arrival_time == 'afternoon':
                vals['dinner_qty'] = stay.guest_qty
        elif self.date == stay.departure_date:
            if stay.departure_time == 'morning':
                return {}
            elif stay.departure_time == 'afternoon':
                vals['lunch_qty'] = stay.guest_qty
            elif stay.departure_time == 'evening':
                vals['lunch_qty'] = stay.guest_qty
                vals['dinner_qty'] = stay.guest_qty
        else:
            vals.update({
                'lunch_qty': stay.guest_qty,
                'dinner_qty': stay.guest_qty,
                'bed_night_qty': stay.guest_qty,
                })
        if not stay.company_id.default_refectory_id:
            raise UserError(_("Missing default refectory on the company '%s'.") % (
                stay.company_id.display_name))
        if stay.no_meals:
            vals.update({
                'lunch_qty': 0, 'dinner_qty': 0, 'refectory_id': False})
        return vals

    def generate(self):
        self.ensure_one()
        lines_to_delete = self.env['stay.line'].search([
            ('date', '=', self.date),
            ('stay_id', '!=', False),
            ('company_id', '=', self.company_id.id),
            ])
        if lines_to_delete:
            lines_to_delete.unlink()
        stays = self.env['stay.stay'].search([
            ('arrival_date', '<=', self.date),
            ('departure_date', '>=', self.date),
            ('company_id', '=', self.company_id.id),
            ])
        if not stays:
            raise UserError(_('No stay for this date.'))
        for stay in stays:
            vals = self._prepare_stay_line(stay)
            if vals:
                self.env['stay.line'].create(vals)

        action = self.env.ref('stay.stay_line_action').sudo().read([])[0]
        action['domain'] = [('date', '=', self.date)]
        return action
