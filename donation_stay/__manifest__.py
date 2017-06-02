# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Donation Stay',
    'version': '10.0.1.0.0',
    'category': 'Lodging',
    'license': 'AGPL-3',
    'summary': 'Create donations from a stay',
    'author': 'Barroux Abbey, Akretion, Odoo Community Association (OCA)',
    'website': 'http://www.barroux.org',
    'depends': ['donation', 'stay'],
    'data': [
        'wizard/create_donation_stay_view.xml',
        'stay_view.xml',
        'donation_stay_data.xml',
        ],
    'demo': [],
    'installable': True,
}
