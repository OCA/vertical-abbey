# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class MassJournalValidate(models.TransientModel):
    _name = "mass.journal.validate"
    _description = "Validate Masses Journal"

    @api.model
    def _get_default_start_date(self):
        line = self.env["mass.line"].search(
            [("state", "=", "draft")], limit=1, order="date asc"
        )
        if line:
            journal_date = line.date
        else:
            journal_date = fields.Date.context_today(self)
        return journal_date

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    start_date = fields.Date(
        "Start Date",
        required=True,
        default=lambda self: self._get_default_start_date(),
    )
    end_date = fields.Date(
        "End Date",
        required=True,
        compute="_compute_end_date",
        readonly=False,
        store=True,
    )

    @api.depends("start_date")
    def _compute_end_date(self):
        for wiz in self:
            if wiz.start_date and (not wiz.end_date or wiz.end_date < wiz.start_date):
                wiz.end_date = wiz.start_date

    def _prepare_mass_validation_move(self, lines):
        company = self.company_id
        movelines = []
        stock_acc2amount = defaultdict(float)  # key = account_id ; value = amount
        income_acc2amount = defaultdict(float)
        # key = (account_id, analytic_account_id) ; value = amount
        comp_cur = company.currency_id
        for line in lines:
            amount = line.unit_offering
            if not comp_cur.is_zero(amount):
                stock_account_id = line.request_id.stock_account_id.id
                if not stock_account_id:
                    raise UserError(
                        _("Stock account is not set on mass request '%s'.")
                        % line.request_id.display_name
                    )

                stock_acc2amount[stock_account_id] += amount

                income_account_id = line.product_id._get_product_accounts()["income"].id
                if not income_account_id:
                    raise UserError(
                        _("Income account is not set for product '%s'.")
                        % line.product_id.display_name
                    )
                income_analytic_account_id = (
                    line.request_id.analytic_account_id.id or False
                )
                key = (income_account_id, income_analytic_account_id)
                income_acc2amount[key] += amount

        if not stock_acc2amount:
            return False

        for stock_account_id, amount in stock_acc2amount.items():
            movelines.append(
                (
                    0,
                    0,
                    {
                        "credit": 0,
                        "debit": amount,
                        "account_id": stock_account_id,
                        "analytic_account_id": False,
                    },
                )
            )

        for (
            income_account_id,
            income_analytic_account_id,
        ), amount in income_acc2amount.items():
            movelines.append(
                (
                    0,
                    0,
                    {
                        "debit": 0,
                        "credit": amount,
                        "account_id": income_account_id,
                        "analytic_account_id": income_analytic_account_id,
                    },
                )
            )

        vals = {
            "journal_id": company.mass_validation_journal_id.id,
            "date": lines[0].date,
            "ref": _("Masses"),
            "company_id": company.id,
            "line_ids": movelines,
        }
        return vals

    def validate_journal(self):
        self.ensure_one()
        company = self.company_id
        if not company.mass_validation_journal_id:
            raise UserError(
                _("Missing Mass Validation Journal on company '%s'.")
                % company.display_name
            )
        if self.start_date > self.end_date:
            raise UserError(
                _(
                    "The start date (%(start_date)s) is after the end date (%(end_date)s).",
                    start_date=format_date(self.env, self.start_date),
                    end_date=format_date(self.env, self.end_date),
                )
            )

        # Search draft mass lines on the date of the wizard
        line_ids = []
        date = self.start_date
        while date <= self.end_date:
            vals = {"state": "done"}
            lines = self.env["mass.line"].search(
                [
                    ("date", "=", date),
                    ("company_id", "=", company.id),
                ]
            )
            if lines:
                # Create account move
                move_vals = self._prepare_mass_validation_move(lines)
                if move_vals:
                    move = self.env["account.move"].create(move_vals)
                    vals["move_id"] = move.id
                    if company.mass_post_move:
                        move.action_post()

                # Update mass lines
                lines.write(vals)
                line_ids += lines.ids
            date += timedelta(1)

        if not line_ids:
            raise UserError(
                _(
                    "No mass to validate between %(start_date)s and %(end_date)s.",
                    start_date=format_date(self.env, self.start_date),
                    end_date=format_date(self.env, self.end_date),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mass.mass_line_action")
        action["domain"] = [("id", "in", line_ids)]
        return action
