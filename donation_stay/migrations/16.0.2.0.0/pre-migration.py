# Copyright 2024 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_column_renames = {
    "stay_stay": [("donation_id", None)],
}


@openupgrade.migrate()
def migrate(env, version):
    # The column donation_id doesn't exist on stay_stay if you upgrade
    # directly from 10.0 to 14.0.2.0.0
    if openupgrade.column_exists(env.cr, "stay_stay", "donation_id"):
        openupgrade.rename_columns(env.cr, _column_renames)
