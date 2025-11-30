# Copyright 2022 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Matthieu Dubois <dubois.matthieu@tutanota.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class StayLineMassUpdate(models.TransientModel):
    _name = "stay.line.mass.update"
    _description = "wizard to mass update lines"

    stay_id = fields.Many2one("stay.stay", required=True, readonly=True)
    refectory_id = fields.Many2one("stay.refectory", string="New Refectory")
    no_breakfast = fields.Boolean(string="No Breakfasts")
    no_lunch = fields.Boolean(string="No Lunches")
    no_dinner = fields.Boolean(string="No Dinners")
    no_bed_night = fields.Boolean(string="No Bed Nights")
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert self._context.get("active_model") == "stay.stay"
        stay_id = self._context.get("active_id")
        stay = self.env["stay.stay"].browse(stay_id)
        today = fields.Date.context_today(self)
        start_date = stay.arrival_date < today and today or stay.arrival_date
        end_date = stay.departure_date
        res.update(
            {
                "stay_id": stay_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        return res

    def _prepare_write_stay_line(self):
        vals = {}
        if self.no_breakfast:
            vals["breakfast_qty"] = 0
        if self.no_lunch:
            vals["lunch_qty"] = 0
        if self.no_dinner:
            vals["dinner_qty"] = 0
        if self.no_bed_night:
            vals["bed_night_qty"] = 0
        if self.refectory_id:
            vals["refectory_id"] = self.refectory_id.id
        return vals

    def _prepare_write_stay(self):
        vals = {}
        if self.refectory_id:
            vals["refectory_id"] = self.refectory_id.id
        return vals

    def apply(self):
        self.ensure_one()
        if self.start_date > self.end_date:
            raise UserError(
                _(
                    "The start date (%(start_date)s) is after the end date (%(end_date)s).",
                    start_date=format_date(self.env, self.start_date),
                    end_date=format_date(self.env, self.end_date),
                )
            )
        vals = self._prepare_write_stay_line()
        if not vals:
            raise UserError(
                _(
                    "You must check at least one option! You didn't check any... "
                    "To reset to default setttings, please use the appropriate "
                    "wizard if installed."
                )
            )
        lines = self.env["stay.line"].search(
            [
                ("stay_id", "=", self.stay_id.id),
                ("date", ">=", self.start_date),
                ("date", "<=", self.end_date),
            ]
        )
        if not lines:
            raise UserError(_("No stay lines to update."))
        lines.write(vals)
        self.stay_id.write(self._prepare_write_stay())
