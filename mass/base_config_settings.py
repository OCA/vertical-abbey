# -*- coding: utf-8 -*-
# Copyright 2017-2019 Barroux Abbey (www.barroux.org)
# Copyright 2017-2019 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    mass_validation_account_id = fields.Many2one(
        related='company_id.mass_validation_account_id')
    mass_validation_analytic_account_id = fields.Many2one(
        related='company_id.mass_validation_analytic_account_id')
    mass_validation_journal_id = fields.Many2one(
        related='company_id.mass_validation_journal_id')
    mass_post_move = fields.Boolean(related='company_id.mass_post_move')
