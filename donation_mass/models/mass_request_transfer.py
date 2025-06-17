# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MassRequestTransfer(models.Model):
    _inherit = "mass.request.transfer"

    def validate(self):
        res = super().validate()
        stock_account = self.company_id.mass_stock_account_id
        if self.move_id.state == "posted" and stock_account.reconcile:
            total = 0.0
            to_rec = self.env["account.move.line"]
            for line in self.move_id.line_ids:
                if line.account_id == stock_account:
                    total += line.balance
                    to_rec |= line
            for mass_req in self.mass_request_ids:
                if (
                    mass_req.donation_id.move_id
                    and mass_req.donation_id.move_id.state == "posted"
                ):
                    for line in mass_req.donation_id.move_id.line_ids:
                        # I add "line not in to_rec" because several mass requests can
                        # be in the same donation and therefore have the same account.move
                        if line.account_id == stock_account and line not in to_rec:
                            total += line.balance
                            to_rec |= line
            if self.company_id.currency_id.is_zero(total):
                to_rec.reconcile()
        return res
