# -*- encoding: utf-8 -*-
##############################################################################
#
#    Mass module for Odoo
#    Copyright (C) 2014-2015 Barroux Abbey (www.barroux.org)
#    Copyright (C) 2014-2015 Akretion France (www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class MassRequestsToTransfer(models.TransientModel):
    _name = 'mass.requests.to.transfer'
    _description = "Select Mass Requests to Transfer"

    mass_request_ids = fields.Many2many(
        'mass.request', column1='mass_request_id', column2='wizard_id',
        string="Mass Requests to Transfer")

    @api.multi
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
