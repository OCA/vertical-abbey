# Copyright 2025 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stay",
    "version": "14.0.2.0.0",
    "category": "Lodging",
    "license": "AGPL-3",
    "summary": "API for stay module",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/vertical-abbey",
    "depends": ["stay", "fastapi"],
    "external_dependencies": {"python": ["fastapi", "pydantic<2"]},
    "data": [
        "data/res_users.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "wizards/stay_create_partner_view.xml",
        "wizards/res_config_settings_view.xml",
        "views/stay_stay.xml",
        "data/mail_template.xml",
    ],
    "installable": True,
}
