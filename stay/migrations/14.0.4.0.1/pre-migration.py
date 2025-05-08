# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        UPDATE ir_model_data SET noupdate=null
        WHERE model='mail.template' AND module='stay' and name='stay_notify'
        """
    )
