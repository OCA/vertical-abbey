# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Donation Stay",
    "version": "16.0.2.0.0",
    "category": "Lodging",
    "license": "AGPL-3",
    "summary": "Create donations from a stay",
    "author": "Barroux Abbey, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/vertical-abbey",
    "depends": ["donation", "stay"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/create_donation_stay_view.xml",
        "wizard/res_config_settings.xml",
        "views/donation.xml",
        "views/stay.xml",
    ],
    "demo": ["demo/demo.xml"],
    "installable": True,
}
