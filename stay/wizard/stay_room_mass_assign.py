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
        if stay.state not in ("draft", "confirm", "current"):
            raise UserError(
                _("Stay '%s' is not in Confirmed nor Current state.")
                % stay.display_name
            )
        res["stay_id"] = self._context.get("active_id")
        return res

    stay_id = fields.Many2one("stay.stay", readonly=True)
    company_id = fields.Many2one(related="stay_id.company_id")
    group_id = fields.Many2one(related="stay_id.group_id")
    assign_type = fields.Selection(
        [
            ("single", "One Guest per Room"),
            ("full", "Maximum Capacity"),
        ],
        string="Assignation",
        default="single",
        required=True,
    )
    conflict_room_ids = fields.Many2many(
        "stay.room", compute="_compute_conflict_room_ids", string="Conflict Rooms"
    )
    room_ids = fields.Many2many(
        "stay.room",
        string="Rooms",
        required=True,
        domain="[('id', 'not in', conflict_room_ids), ('company_id', '=', company_id), "
        "('group_id', 'in', (False, group_id))]",
    )

    @api.depends("stay_id")
    def _compute_conflict_room_ids(self):
        # adapted from the code of stay.room.assign
        for wiz in self:
            stay = wiz.stay_id
            company_id = stay.company_id.id
            potential_excl_room_ids = (
                self.env["stay.room"]
                .search(
                    [
                        ("allow_simultaneous", "=", False),
                        ("company_id", "=", company_id),
                    ]
                )
                .ids
            )
            conflict_domain = stay._get_assign_base_conflict_domain()
            conflict_domain.append(("room_id", "in", potential_excl_room_ids))
            # One potential cause of problem: if the user deletes an assign line
            # and creates a new one (without save in between), Odoo will not
            # propose the room of the deleted assign line (until a new "save")
            # because the deleted assign line still exists in DB
            conflict_assigns = self.env["stay.room.assign"].search_read(
                conflict_domain, ["room_id"]
            )
            conflict_room_ids = {cass["room_id"][0] for cass in conflict_assigns}
            wiz.conflict_room_ids = list(conflict_room_ids)

    def _prepare_room_assign(self, room, qty_left_to_assign, assign_type):
        if assign_type == "full":
            if qty_left_to_assign <= room.bed_qty:
                guest_qty = qty_left_to_assign
            else:
                guest_qty = room.bed_qty
        else:
            guest_qty = 1
        return {
            "room_id": room.id,
            "guest_qty": guest_qty,
            "stay_id": self.stay_id.id,
        }

    def run(self):
        self.ensure_one()
        existing_rooms = {}
        for line in self.stay_id.room_assign_ids:
            existing_rooms[line.room_id.id] = True
        vals_list = []
        qty_left_to_assign = self.stay_id.guest_qty_to_assign
        assign_type = self.assign_type
        for room in self.room_ids:
            if room.id not in existing_rooms and qty_left_to_assign > 0:
                vals = self._prepare_room_assign(room, qty_left_to_assign, assign_type)
                qty_left_to_assign -= vals["guest_qty"]
                vals_list.append(vals)
        self.env["stay.room.assign"].create(vals_list)
