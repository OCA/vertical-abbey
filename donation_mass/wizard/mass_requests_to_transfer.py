# Copyright 2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class MassRequestsToTransfer(models.TransientModel):
    _inherit = 'mass.requests.to.transfer'

    request_ids = fields.Many2many(
        domain="[('state', '=', 'waiting'), ('celebrant_id', '=', False), ('request_date', '=', False), ('company_id', '=', company_id), ('donation_line_id', '!=', False)]")
