# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StayType(models.Model):
    _name = "stay.type"
    _description = "Stay Type"
    _order = "sequence, id"

    sequence = fields.Integer()
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    update_url = fields.Char(string="Update URL")

    _sql_constraints = [
        ("name_uniq", "unique(name)", "This stay type already exists."),
    ]
