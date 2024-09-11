# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MassJournalValidate(models.TransientModel):
    _name = "mass.journal.validate"
    _description = "Validate Masses Journal"

    @api.model
    def _get_default_journal_date(self):
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
    journal_date = fields.Date(
        "Journal Date",
        required=True,
        default=lambda self: self._get_default_journal_date(),
    )

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
            "date": self.journal_date,
            "ref": _("Masses"),
            "company_id": company.id,
            "line_ids": movelines,
        }
        return vals

    def validate_journal(self):
        self.ensure_one()
        date = self.journal_date
        company = self.company_id
        # Search draft mass lines on the date of the wizard
        lines = self.env["mass.line"].search(
            [("date", "=", date), ("company_id", "=", company.id)]
        )
        vals = {"state": "done"}
        if not company.mass_validation_journal_id:
            raise UserError(
                _("Missing Mass Validation Journal on company '%s'.")
                % company.display_name
            )
        # Create account move
        move_vals = self._prepare_mass_validation_move(lines)
        if move_vals:
            move = self.env["account.move"].create(move_vals)
            vals["move_id"] = move.id
            if company.mass_post_move:
                move.action_post()

        # Update mass lines
        lines.write(vals)

        action = self.env.ref("mass.mass_line_action").sudo().read([])[0]
        action["domain"] = [("id", "in", lines.ids)]
        return action
