# Copyright 2023 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

column_renames = {
    "stay_stay": [("room_id", None)],
}


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    openupgrade.rename_columns(env.cr, column_renames)
