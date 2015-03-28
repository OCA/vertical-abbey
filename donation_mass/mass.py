# -*- encoding: utf-8 -*-
##############################################################################
#
#    Donation Mass module for Odoo
#    Copyright (C) 2014-2015 Barroux Abbey (www.barroux.org)
#    Copyright (C) 2014-2015 Akretion France (www.akretion.com)
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

from openerp import models, fields


class mass_request(models.Model):
    _inherit = "mass.request"

    donation_line_id = fields.Many2one(
        'donation.line', string='Related Donation Line', readonly=True)
    donation_id = fields.Many2one(
        'donation.donation', related='donation_line_id.donation_id',
        string="Related Donation", readonly=True, store=True)
