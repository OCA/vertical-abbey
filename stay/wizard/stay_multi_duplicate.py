# Copyright 2022 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class StayMultiDuplicate(models.TransientModel):
    _name = 'stay.multi.duplicate'
    _description = 'Multi Stay Duplicate Wizard'

    stay_id = fields.Many2one('stay.stay', required=True, readonly=True)
    frequency = fields.Selection([
        ('weekly', 'Weekly')], required=True, default='weekly')
    start_date = fields.Date(required=True, default=fields.Date.context_today)
    end_date = fields.Date(required=True)
    create_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ], default='draft', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert self._context.get('active_model') == 'stay.stay'
        res['stay_id'] = self._context.get('active_id')
        return res

    def run(self):
        self.ensure_one()
        print('self.stay_id=', self.stay_id)
        if self.end_date <= self.start_date:
            raise UserError(_("The end date (%s) must be after the start_date (%s)!") % (format_date(self.env, self.end_date), format_date(self.env, self.start_date)))
        if self.frequency == 'weekly' and self.start_date + timedelta(days=7) > self.end_date:
            raise UserError(_("The interval between the start date (%s) and the end date (%s) is under one week.") % (format_date(self.env, self.start_date), format_date(self.env, self.end_date)))

