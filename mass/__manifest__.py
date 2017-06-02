# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>

{
    'name': 'Mass',
    'version': '10.0.1.0.0',
    'category': 'Christian Religion',
    'license': 'AGPL-3',
    'summary': 'Manage Mass',
    'author': 'Barroux Abbey, Akretion, Odoo Community Association (OCA)',
    'website': 'http://www.barroux.org',
    'depends': ['account'],
    'data': [
        'security/mass_security.xml',
        'security/ir.model.access.csv',
        'wizard/select_mass_requests_to_transfer_view.xml',
        'wizard/generate_mass_journal_view.xml',
        'wizard/validate_mass_journal_view.xml',
        'wizard/swap_celebrant_view.xml',
        'mass_view.xml',
        'mass_data.xml',
        'partner_view.xml',
        'product_view.xml',
        'report.xml',
        'views/report_massrequesttransfer.xml',
        'views/report_massline.xml',
        'base_config_settings_view.xml',
        ],
    'demo': ['mass_demo.xml'],
    'installable': True,
}
