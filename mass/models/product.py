# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mass = fields.Boolean(string="Is a Mass")
    mass_request_type_id = fields.Many2one(
        "mass.request.type", string="Mass Request Type", ondelete="restrict"
    )

    @api.onchange("mass")
    def mass_change(self):
        if self.mass:
            self.type = "service"
            self.sale_ok = False


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("mass")
    def mass_change(self):
        if self.mass:
            self.type = "service"
            self.sale_ok = False
