# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    default_refectory_id = fields.Many2one(
        related='company_id.default_refectory_id', string='Default Refectory')
