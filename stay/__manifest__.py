# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Brother Bernard <informatique@barroux.org>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stay',
    'version': '10.0.1.0.0',
    'category': 'Lodging',
    'license': 'AGPL-3',
    'summary': 'Simple management of stays and meals',
    'author': 'Barroux Abbey, Akretion, Odoo Community Association (OCA)',
    'website': 'http://www.barroux.org',
    'depends': ['report', 'mail', 'web_timeline'],
    'external_dependencies': {'python': ['xlsxwriter']},
    'data': [
        'security/stay_security.xml',
        'stay_view.xml',
        'stay_data.xml',
        'base_config_settings_view.xml',
        'wizard/stay_journal_generate_view.xml',
        'wizard/stay_journal_print_view.xml',
        'wizard/stay_stay_xlsx_view.xml',
        'security/ir.model.access.csv',
        'report.xml',
        'report/report_stay_journal.xml',
        'partner_view.xml',
        'data/cron.xml',
        'data/mail_template.xml',
        ],
    'demo': ['stay_demo.xml'],
    'application': True,
    'installable': True,
}
