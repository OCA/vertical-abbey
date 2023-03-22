# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    detailed_type = fields.Selection(
        selection_add=[
            ("donation_mass", "Mass"),
        ],
        ondelete={
            "donation_mass": "set service",
        },
    )

    def _detailed_type_mapping(self):
        res = super()._detailed_type_mapping()
        res["donation_mass"] = "service"
        return res

    mass_request_type_id = fields.Many2one("mass.request.type", ondelete="restrict")
