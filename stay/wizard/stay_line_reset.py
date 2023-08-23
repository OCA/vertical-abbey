# Copyright 2022 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Matthieu Dubois <dubois.matthieu@tutanota.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class StayLineReset(models.TransientModel):
    _name = "stay.line.reset"
    _description = "wizard to reset all lines to default values"

    stay_id = fields.Many2one("stay.stay", required=True, readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert self._context.get("active_model") == "stay.stay"
        res["stay_id"] = self._context.get("active_id")
        return res

    def reset_lines(self):
        self.ensure_one()
        self.stay_id.line_ids.unlink()
        self.stay_id._update_lines()
