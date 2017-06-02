# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class MassRequestsToTransfer(models.TransientModel):
    _name = 'mass.requests.to.transfer'
    _description = "Select Mass Requests to Transfer"

    mass_request_ids = fields.Many2many(
        'mass.request', column1='mass_request_id', column2='wizard_id',
        string="Mass Requests to Transfer")

    def add_to_transfer(self):
        self.ensure_one()
        assert self._context['active_model'] == 'mass.request.transfer', \
            'active_model must be mass.request.transfer'
        if self.mass_request_ids:
            mass_request_transfer = self.env['mass.request.transfer'].browse(
                self._context['active_id'])
            mass_request_ids = \
                [(4, request.id) for request in self.mass_request_ids]
            mass_request_transfer.mass_request_ids = mass_request_ids
        return
