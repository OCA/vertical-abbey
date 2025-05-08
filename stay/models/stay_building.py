# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StayBuilding(models.Model):
    _name = "stay.building"
    _description = "Buildings"
    _order = "sequence, id"

    sequence = fields.Integer()
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    room_ids = fields.One2many("stay.room", "building_id", string="Rooms")

    _sql_constraints = [("name_uniq", "unique(name)", "This building already exists.")]
