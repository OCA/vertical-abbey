# -*- encoding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('mass')
    def mass_change(self):
        super(ProductTemplate, self).mass_change()
        if self.mass:
            self.donation = True


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('mass')
    def mass_change(self):
        super(ProductProduct, self).mass_change()
        if self.mass:
            self.donation = True
