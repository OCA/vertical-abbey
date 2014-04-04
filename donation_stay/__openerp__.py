# -*- encoding: utf-8 -*-
##############################################################################
#
#    Donation Stay module for OpenERP
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
    'name': 'Donation Stay',
    'version': '0.1',
    'category': 'Lodging',
    'license': 'AGPL-3',
    'summary': 'Create donations from a stay',
    'description': """
Donation Stay
=============

This module adds a wizard to create a donation from the form view of a stay.

It has been developped by brother Bernard and brother Irénée from Barroux Abbey and by Alexis de Lattre from Akretion.
    """,
    'author': 'Barroux, Akretion',
    'website': 'http://www.barroux.org',
    'depends': ['donation_tax_receipt', 'stay'],
    'data': [
        'wizard/create_donation_stay_view.xml',
        'stay_view.xml',
        'donation_stay_data.xml',
        ],
    'demo': [],
    'active': False,
}
