# -*- encoding: utf-8 -*-
##############################################################################
#
#    Mass module for OpenERP
#    Copyright (C) 2014 Artisanat Monastique de Provence
#                       (http://www.barroux.org)
#    @author
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


{
    'name': 'Mass',
    'version': '0.1',
    'category': 'Christian Religion',
    'license': 'AGPL-3',
    'summary': 'Manage Mass',
    'description': """
Mass
====

This module manages planning of masses.

It has been developped by brother Bernard and brother Irénée from Barroux Abbey and by Alexis de Lattre from Akretion.
    """,
    'author': 'Barroux, Akretion',
    'website': 'http://www.barroux.org',
    'depends': ['product', 'report_webkit', 'account', 'base_headers_webkit'],
    'data': [
        'wizard/select_mass_requests_to_transfer_view.xml',
        'wizard/generate_mass_journal_view.xml',
        'wizard/validate_mass_journal_view.xml',
        'wizard/swap_celebrant_view.xml',
        'mass_view.xml',
        'mass_data.xml',
        'partner_view.xml',
        'product_view.xml',
        'company_view.xml',
        'security/mass_security.xml',
        'security/ir.model.access.csv',
        'report.xml',
        ],
    'demo': ['mass_demo.xml'],
    'active': False,
}
