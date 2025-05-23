# Copyright 2025 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stay",
    "version": "14.0.3.1.0",
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
        "security/ir.model.access.csv",
        "wizards/stay_create_partner_view.xml",
        "views/stay_stay.xml",
        "views/stay_type.xml",
        "views/res_partner_title.xml",
        "data/mail_template.xml",
    ],
    "post_init_hook": "stay_api_postinstall",
    "installable": True,
}
