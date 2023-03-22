# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    mass_stock_account_id = fields.Many2one(
        "account.account",
        domain=[("deprecated", "!=", True)],
        check_company=True,
    )
    mass_validation_journal_id = fields.Many2one("account.journal", check_company=True)
    mass_post_move = fields.Boolean(string="Post Move", default=True)
