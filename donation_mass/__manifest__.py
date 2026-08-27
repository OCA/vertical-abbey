# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>

{
    "name": "Donation Mass",
    "version": "18.0.1.0.0",
    "category": "Religion",
    "license": "AGPL-3",
    "summary": "Manage Mass",
    "author": "Barroux Abbey, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/vertical-abbey",
    "depends": ["donation"],
    "data": [
        "security/mass_security.xml",
        "security/ir.model.access.csv",
        "wizards/mass_journal_generate_view.xml",
        "wizards/mass_journal_validate_view.xml",
        "wizards/swap_celebrant_view.xml",
        "wizards/res_config_settings_view.xml",
        "reports/report.xml",
        "reports/report_massrequesttransfer.xml",
        "reports/report_massline.xml",
        "data/mass_data.xml",
        "views/mass.xml",
        "views/donation.xml",
        "views/product.xml",
        "views/res_partner.xml",
    ],
    "demo": ["demo/mass.xml"],
    "installable": True,
}
