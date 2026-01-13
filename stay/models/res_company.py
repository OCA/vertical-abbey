# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    default_refectory_id = fields.Many2one(
        "stay.refectory",
        string="Default Refectory",
        ondelete="restrict",
        check_company=True,
    )
    # Warning: explicit definition of the relation table is needed here
    # because many modules have a M2M fields from res.company to res.users
    # and we must avoid a table name collision
    stay_notify_user_ids = fields.Many2many(
        "res.users",
        relation="stay_notify_company_user_rel",
        column1="res_company_id",
        column2="res_users_id",
        string="Users Notified by E-mail for Stays without Group",
    )
