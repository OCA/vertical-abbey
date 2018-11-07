# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('stay_ids.partner_id')
    def _compute_stay_count(self):
        res = self.env['stay.stay'].read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'], ['partner_id'])
        for re in res:
            partner = self.browse(re['partner_id'][0])
            partner.stay_count = re['partner_id_count']

    stay_ids = fields.One2many(
        'stay.stay', 'partner_id', string='Stays')
    stay_count = fields.Integer(
        compute='_compute_stay_count', string="# of Stays", readonly=True)
