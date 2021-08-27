# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class MassRequestsToTransfer(models.TransientModel):
    _name = 'mass.requests.to.transfer'
    _description = "Select Mass Requests to Transfer"

    transfer_id = fields.Many2one('mass.request.transfer', string='Mass Transfer', required=True, readonly=True)
    company_id = fields.Many2one(related='transfer_id.company_id')
    request_ids = fields.Many2many(
        'mass.request', column1='mass_request_id', column2='wizard_id',
        string="Mass Requests to Transfer",
        domain="[('state', '=', 'waiting'), ('celebrant_id', '=', False), ('request_date', '=', False), ('company_id', '=', company_id)]")

    def add_to_transfer(self):
        self.ensure_one()
        if self.request_ids:
            mass_request_ids = \
                [(4, request.id) for request in self.request_ids]
            self.transfer_id.write({'mass_request_ids': mass_request_ids})
        return
