# -*- coding: utf-8 -*-
# © 2017 Barroux Abbey (www.barroux.org)
# © 2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    mass_validation_account_id = fields.Many2one(
        related='company_id.mass_validation_account_id',
        domain=[('deprecated', '!=', True)])
    mass_validation_journal_id = fields.Many2one(
        related='company_id.mass_validation_journal_id')
    mass_post_move = fields.Boolean(related='company_id.mass_post_move')
