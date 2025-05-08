# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from random import randint

from odoo import fields, models


class StayTag(models.Model):
    _name = "stay.tag"
    _description = "Stay Tags"

    sequence = fields.Integer()
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    color = fields.Integer(default=lambda self: randint(1, 11))

    _sql_constraints = [("name_uniq", "unique(name)", "This tag already exists.")]
