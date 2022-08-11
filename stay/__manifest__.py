# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stay",
    "version": "14.0.1.0.0",
    "category": "Lodging",
    "license": "AGPL-3",
    "summary": "Simple management of stays and meals",
    "author": "Barroux Abbey, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/vertical-abbey",
    "depends": ["mail", "web_timeline"],
    "external_dependencies": {"python": ["xlsxwriter"]},
    "data": [
        "security/stay_security.xml",
        "views/stay_menu.xml",
        "wizard/res_config_settings_view.xml",
        "wizard/stay_journal_print_view.xml",
        "wizard/stay_toclean_print_view.xml",
        "wizard/stay_stay_xlsx_view.xml",
        "wizard/stay_multi_duplicate_view.xml",
        "wizard/stay_line_mass_update_view.xml",
        "wizard/stay_line_reset_view.xml",
        "wizard/stay_room_mass_assign_view.xml",
        "views/stay.xml",
        "views/stay_iframe.xml",
        "data/sequence.xml",
        "security/ir.model.access.csv",
        "report/report.xml",
        "report/report_stay_journal.xml",
        "views/res_partner.xml",
        "data/cron.xml",
        "data/mail_template.xml",
    ],
    "demo": ["demo/stay_demo.xml"],
    "application": True,
    "installable": True,
}
