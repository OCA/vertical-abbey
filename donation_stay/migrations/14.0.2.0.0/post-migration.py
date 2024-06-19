# Copyright 2024 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    old_column = openupgrade.get_legacy_name("donation_id")
    if openupgrade.column_exists(env.cr, "stay_stay", old_column):
        openupgrade.m2o_to_x2m(
            env.cr,
            env["stay.stay"],
            "stay_stay",
            "donation_ids",
            old_column,
        )
        sso = env["stay.stay"]
        ids = [x.get("id") for x in sso.search_read([], ["id"])]
        env.all.tocompute[sso._fields["donation_total"]].update(ids)
        sso.recompute()
