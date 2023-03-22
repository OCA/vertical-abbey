# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    celebrant = fields.Selection(
        [
            ("internal", "Internal"),
            ("external", "External"),
        ],
    )

    @api.constrains("celebrant", "is_company")
    def _check_celebrant(self):
        for partner in self:
            if partner.is_company and partner.celebrant == "internal":
                raise ValidationError(_("An internal celebrant cannot be a company."))
