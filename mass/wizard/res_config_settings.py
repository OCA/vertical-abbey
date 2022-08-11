# Copyright 2017-2021 Barroux Abbey (www.barroux.org)
# Copyright 2017-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mass_stock_account_id = fields.Many2one(
        related="company_id.mass_stock_account_id",
        readonly=False,
        domain="[('company_id', '=', company_id), ('deprecated', '=', False)]",
    )
    mass_validation_journal_id = fields.Many2one(
        related="company_id.mass_validation_journal_id",
        readonly=False,
        domain="[('company_id', '=', company_id), ('type', 'in', ('sale', 'general'))]",
    )
    mass_post_move = fields.Boolean(related="company_id.mass_post_move", readonly=False)
