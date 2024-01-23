# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>

{
    "name": "Mass",
    "version": "16.0.1.0.0",
    "category": "Christian Religion",
    "license": "AGPL-3",
    "summary": "Manage Mass",
    "author": "Barroux Abbey, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/vertical-abbey",
    "depends": ["account"],
    "data": [
        "security/mass_security.xml",
        "security/ir.model.access.csv",
        "report/report.xml",
        "report/report_massrequesttransfer.xml",
        "report/report_massline.xml",
        "wizard/mass_journal_generate_view.xml",
        "wizard/mass_journal_validate_view.xml",
        "wizard/swap_celebrant_view.xml",
        "views/mass.xml",
        "data/mass_data.xml",
        "views/res_partner.xml",
        "views/product.xml",
        "wizard/res_config_settings_view.xml",
    ],
    "demo": ["demo/mass_demo.xml"],
    "application": True,
    "installable": True,
}
