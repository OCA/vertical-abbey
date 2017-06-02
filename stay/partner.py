# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.depends('stay_ids.partner_id')
    def _stay_count(self):
        # The current user may not have access rights for stays
        try:
            self.stay_count = len(self.stay_ids)
        except:
            self.stay_count = 0

    stay_ids = fields.One2many(
        'stay.stay', 'partner_id', string='Stays')
    stay_count = fields.Integer(
        compute='_stay_count', string="# of Stays", readonly=True)
