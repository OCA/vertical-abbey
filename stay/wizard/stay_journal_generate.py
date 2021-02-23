# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from dateutil.relativedelta import relativedelta


class StayJournalGenerate(models.TransientModel):
    _name = 'stay.journal.generate'
    _description = 'Generate the Stay Lines'
    _rec_name = 'date'

    @api.model
    def _default_date(self):
        today_str = fields.Date.context_today(self)
        today_dt = fields.Date.from_string(today_str)
        tomorrow_dt = today_dt + relativedelta(days=1)
        return tomorrow_dt

    date = fields.Date(string='Date', required=True, default=_default_date)

    @api.model
    def _prepare_stay_line(self, stay, date):
        vals = {
            'date': date,
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
        if date == stay.arrival_date and date == stay.departure_date:
            if stay.arrival_time == 'morning':
                # then departure_time is afternoon or evening
                vals['lunch_qty'] = stay.guest_qty
                if stay.departure_time == 'evening':
                    vals['dinner_qty'] = stay.guest_qty
            elif stay.arrival_time == 'afternoon':
                # then departure_time is evening
                vals['dinner_qty'] = stay.guest_qty
        elif date == stay.arrival_date:
            vals['bed_night_qty'] = stay.guest_qty
            if stay.arrival_time == 'morning':
                vals['lunch_qty'] = stay.guest_qty
                vals['dinner_qty'] = stay.guest_qty
            elif stay.arrival_time == 'afternoon':
                vals['dinner_qty'] = stay.guest_qty
        elif date == stay.departure_date:
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
            msg = _("Missing default refectory on the company '%s'.") % (
                stay.company_id.name)
            action = self.env.ref('base.action_res_company_form')
            raise RedirectWarning(
                msg, action.id, 'Go to the Company')
        if stay.no_meals:
            vals.update({
                'lunch_qty': 0, 'dinner_qty': 0, 'refectory_id': False})
        return vals

    def generate(self):
        self.ensure_one()
        lines_to_delete = self.env['stay.line'].search(
            [('date', '=', self.date), ('stay_id', '!=', False)])
        if lines_to_delete:
            lines_to_delete.unlink()
        stays = self.env['stay.stay'].search([
            ('arrival_date', '<=', self.date),
            ('departure_date', '>=', self.date),
            ])
        if not stays:
            raise UserError(_('No stay for this date.'))
        for stay in stays:
            vals = self._prepare_stay_line(stay, self.date)
            if vals:
                self.env['stay.line'].create(vals)

        action = self.env['ir.actions.act_window'].for_xml_id(
            'stay', 'stay_line_action')
        action.update({
            'view_mode': 'tree,form',
            'domain': [('date', '=', self.date)],
            })
        return action
