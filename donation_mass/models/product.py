# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.onchange("mass")
    def mass_donation_change(self):
        if self.mass:
            self.donation = True


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("mass")
    def mass_donation_change(self):
        if self.mass:
            self.donation = True
