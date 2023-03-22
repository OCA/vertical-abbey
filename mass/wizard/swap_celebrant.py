# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class SwapCelebrant(models.TransientModel):
    _name = "swap.celebrant"
    _description = "Swap Celebrant"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert (
            self._context["active_model"] == "mass.line"
        ), "active_model should be mass.line"
        line_ids = self._context["active_ids"]
        if len(line_ids) != 2:
            raise UserError(
                _("You should only select 2 mass lines (%d were selected).")
                % len(line_ids)
            )
        lines = self.env["mass.line"].browse(line_ids)
        if lines[0].date != lines[1].date:
            raise UserError(
                _(
                    "The 2 mass lines that you selected have different dates "
                    "(%(date1)s and %(date2)s). You can swap celebrants only between 2 "
                    "masses of the same date.",
                    date1=format_date(self.env, lines[0].date),
                    date2=format_date(self.env, lines[1].date),
                )
            )
        res["line_ids"] = [(6, 0, lines.ids)]
        return res

    line_ids = fields.Many2many("mass.line", string="Mass Lines to Swap", readonly=True)

    def swap_celebrant(self):
        self.ensure_one()
        lines = self.line_ids
        swapped = {
            lines[0]: lines[1].celebrant_id.id,
            lines[1]: lines[0].celebrant_id.id,
        }
        for line, celebrant_id in swapped.items():
            line.write({"celebrant_id": celebrant_id})
