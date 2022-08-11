# Copyright 2022 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StayTocleanPrint(models.TransientModel):
    _name = "stay.toclean.print"
    _description = "Print to clean report"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    def print_report(self):
        action = (
            self.env.ref("stay.report_stay_toclean")
            .with_context({"discard_logo_check": True})
            .report_action(self)
        )
        return action

    def report_toclean_data(self):
        self.ensure_one()
        sro = self.env["stay.room"]
        sgo = self.env["stay.group"]
        # The result must be orderd by group and by room
        res = {}
        for group in sgo.search([("company_id", "=", self.company_id.id)]):
            res[group.name] = []
        res["none"] = []
        for room in sro.search(
            [("to_clean", "!=", False), ("company_id", "=", self.company_id.id)]
        ):
            group = room.group_id and room.group_id.name or "none"
            res[group].append(room)
        res_final = {}
        # remove empty groups
        for group, rooms in res.items():
            if rooms:
                res_final[group] = rooms
        return res_final
