# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StayRoomMassAssign(models.TransientModel):
    _name = "stay.room.mass.assign"
    _description = "Mass Assignation of Stay Rooms"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        assert self._context.get("active_model") == "stay.stay"
        stay = self.env["stay.stay"].browse(self._context.get("active_id"))
        if stay.state not in ("confirm", "current"):
            raise UserError(
                _("Stay '%s' is not in Confirmed nor Current state.")
                % stay.display_name
            )
        res["stay_id"] = self._context.get("active_id")
        return res

    stay_id = fields.Many2one("stay.stay", readonly=True)
    company_id = fields.Many2one(related="stay_id.company_id")
    group_id = fields.Many2one(related="stay_id.group_id")
    room_ids = fields.Many2many(
        "stay.room",
        string="Rooms",
        required=True,
        domain="[('company_id', '=', company_id), ('group_id', 'in', (False, group_id))]",
    )

    def _prepare_room_assign(self, room):
        return {
            "room_id": room.id,
            "guest_qty": room.bed_qty,
            "stay_id": self.stay_id.id,
        }

    def run(self):
        self.ensure_one()
        existing_rooms = {}
        for line in self.stay_id.room_assign_ids:
            existing_rooms[line.room_id.id] = True
        vals = []
        for room in self.room_ids:
            if room.id not in existing_rooms:
                vals.append(self._prepare_room_assign(room))
        self.env["stay.room.assign"].create(vals)
