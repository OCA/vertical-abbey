# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>

{
    'name': 'Donation Mass',
    'version': '10.0.1.0.0',
    'category': 'Religion',
    'license': 'AGPL-3',
    'summary': 'Ability to create mass from donation lines',
    'author': 'Barroux Abbey, Akretion, Odoo Community Association (OCA)',
    'website': 'http://www.barroux.org',
    'depends': ['donation', 'mass'],
    'data': [
        'mass_view.xml',
        'donation_view.xml',
        'donation_mass_data.xml',
        'wizard/select_mass_requests_to_transfer_view.xml',
        'security/ir.model.access.csv',
        ],
    'demo': ['donation_mass_demo.xml'],
    'installable': True,
}
