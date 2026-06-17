# Copyright 2025 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stay API",
    "version": "18.0.1.0.0",
    "category": "Lodging",
    "license": "AGPL-3",
    "summary": "REST API for stay module",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/vertical-abbey",
    "depends": ["stay", "fastapi", "partner_match_or_create"],
    "external_dependencies": {"python": ["fastapi"]},
    "data": [
        "data/res_users.xml",
        "security/ir.model.access.csv",
        "wizards/res_config_settings_view.xml",
        "views/stay_stay.xml",
        "views/stay_type.xml",
        "data/mail_template.xml",
    ],
    "post_init_hook": "stay_api_postinstall",
    "installable": True,
}
