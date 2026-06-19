# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    donation_type = fields.Selection(
        selection_add=[
            ("mass", "Mass"),
        ],
        ondelete={
            "mass": "set donation",
        },
    )
    mass_request_type_id = fields.Many2one("mass.request.type", ondelete="restrict")

    def _compute_tax_receipt_ok(self):
        for product in self:
            if product.donation_type == "mass":
                product.tax_receipt_ok = False
        return super()._compute_tax_receipt_ok()

    @api.constrains("donation_type", "mass_request_type_id")
    def _check_mass_request_type_id(self):
        for product in self:
            if product.mass_request_type_id and product.donation_type != "mass":
                raise ValidationError(
                    self.env._(
                        "Product %s is linked to a Mass Request Type but it's "
                        "Donation Type is not 'Mass'.",
                        product.display_name,
                    )
                )
