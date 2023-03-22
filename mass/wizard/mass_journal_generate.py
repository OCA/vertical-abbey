# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author Brother Bernard <informatique _at_ barroux.org>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class MassJournalGenerate(models.TransientModel):
    _name = "mass.journal.generate"
    _description = "Generate Masses Journal"

    @api.model
    def _get_default_journal_date(self):
        line = self.env["mass.line"].search([], limit=1, order="date desc")
        if line:
            journal_date = line.date + relativedelta(days=1)
        else:
            journal_date = fields.Date.context_today(self) + relativedelta(days=1)
        return journal_date

    @api.model
    def _default_celebrants(self):
        all_celebrants = self.env["res.partner"].search(
            [("celebrant", "=", "internal")]
        )
        return all_celebrants

    journal_date = fields.Date(
        required=True,
        default=lambda self: self._get_default_journal_date(),
    )
    celebrant_ids = fields.Many2many(
        "res.partner",
        column1="partner_id",
        column2="wizard_id",
        domain=[("celebrant", "=", "internal")],
        string="List of celebrants",
        default=lambda self: self._default_celebrants(),
    )

    @api.model
    def _multi_allowed_dates(self):
        """We return only Christmas date"""
        return ["%s-12-25" % fields.Date.context_today(self).year]

    @api.onchange("journal_date")
    def journal_date_on_change(self):
        line = self.env["mass.line"].search(
            [("date", "=", self.journal_date)], limit=1, order="date desc"
        )
        res = {"warning": {}}
        if line:
            if self.journal_date in self._multi_allowed_dates():
                res["warning"] = {
                    "title": _("Warning"),
                    "message": _(
                        "You are about to generate another journal "
                        "for %s : it is allowed for that date."
                    )
                    % format_date(self.env, self.journal_date),
                }
            else:
                raise UserError(
                    _(
                        "There is already a journal for %s. You cannot generate "
                        "another journal for that date. Odoo has reverted "
                        "to the default date."
                    )
                    % format_date(self.env, self.journal_date)
                )
        return res

    @api.model
    def _prepare_mass_line(self, line, date):
        vals = {
            "request_id": line["request"].id,
            "celebrant_id": line["celebrant_id"],
            "date": date,
            "unit_offering": line["request"].unit_offering,
        }
        return vals

    def generate_journal(self):  # noqa: C901, B007
        self.ensure_one()
        journal_date = self.journal_date
        first_journal = True
        if self.env["mass.line"].search_count([("date", "=", journal_date)]):
            first_journal = False
        if not self.celebrant_ids:
            raise UserError(_("No celebrants were selected !"))
        number_of_celebrants = len(self.celebrant_ids)
        mass_lines = []
        # Retreive mass requests
        # First, requests with request date = journal date and state = started
        if first_journal:
            domain1 = [
                "|",
                ("request_date", "=", journal_date),
                ("state", "=", "started"),
            ]
        else:
            domain1 = [
                ("request_date", "=", journal_date),
                ("uninterrupted", "=", False),
            ]
        requests = self.env["mass.request"].search(
            domain1, order="request_date, donation_date"
        )
        for request in requests:
            if request.uninterrupted or request.celebrant_id:
                iteration = 1
            else:
                iteration = request.mass_remaining_quantity
            for _i in range(0, iteration):
                mass_lines.append(
                    {
                        "request": request,
                        "celebrant_id": request.celebrant_id.id or False,
                    }
                )
        rest = number_of_celebrants - len(mass_lines)
        if rest < 0:
            raise UserError(
                _(
                    "The number of requests for this day exceeds "
                    "the number of celebrants. Please, modify requests."
                )
            )
        if rest > 0:
            # Last, requests with state = waiting (fifo rule)
            if first_journal:
                domain2 = [
                    ("state", "=", "waiting"),
                    ("request_date", "=", False),
                ]
            else:
                domain2 = [
                    ("state", "=", "waiting"),
                    ("request_date", "=", False),
                    ("uninterrupted", "=", False),
                ]
            requests = self.env["mass.request"].search(domain2, order="donation_date")
            for request in requests:
                if request.uninterrupted or request.celebrant_id:
                    iteration = 1
                else:
                    iteration = request.mass_remaining_quantity
                for _i in range(0, iteration):
                    mass_lines.append(
                        {
                            "request": request,
                            "celebrant_id": request.celebrant_id.id or False,
                        }
                    )
                    rest -= 1
                    if rest == 0:
                        break
                if rest == 0:
                    break

        # Record journal
        # Assign a celebrant for each mass
        celebrant_ids = self.celebrant_ids.ids
        origin_celebrant_ids = list(celebrant_ids)  # copy
        # First loop to assign resquested celebrants
        for line in mass_lines:
            celebrant_id = line["celebrant_id"]
            if celebrant_id:
                if celebrant_id in celebrant_ids:
                    celebrant_ids.remove(celebrant_id)
                elif celebrant_id not in origin_celebrant_ids:
                    raise UserError(
                        _(
                            "The celebrant %(celebrant)s has an assigned mass for "
                            "%(partner)s, but he is not available today.",
                            celebrant=line["request"].celebrant_id.display_name,
                            partner=line["request"].partner_id.display_name,
                        )
                    )
                else:
                    raise UserError(
                        _(
                            "More than one mass are assigned "
                            "to the same celebrant %s. Please, modify requests."
                        )
                        % line["request"].celebrant_id.display_name
                    )
        # Second loop to assign a celebrant for the rest of mass lines
        for line in mass_lines:
            celebrant_id = line["celebrant_id"]
            if not celebrant_id:
                celebrant_id = celebrant_ids.pop(0)
                line["celebrant_id"] = celebrant_id
        if len(celebrant_ids) != 0:
            raise UserError(_("%s celebrants were not assigned.") % len(celebrant_ids))

        # Create mass lines
        new_line_ids = []
        for line in mass_lines:
            vals = self._prepare_mass_line(line, journal_date)
            new_line = self.env["mass.line"].create(vals)
            new_line_ids.append(new_line.id)

        action = self.env.ref("mass.mass_line_action").sudo().read([])[0]
        action["domain"] = [("id", "in", new_line_ids)]
        return action
