# Copyright 2023 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.table_exists(env.cr, "stay_room_assign"):
        openupgrade.logged_query(
            env.cr,
            """
            INSERT INTO stay_room_assign
            (
                create_uid, create_date, write_uid, write_date,
                stay_id, room_id, guest_qty,
                group_id, user_id,
                stay_group_id,
                arrival_date, arrival_time, arrival_datetime,
                departure_date, departure_time, departure_datetime,
                partner_id, partner_name, company_id
            )
            SELECT s.create_uid, s.create_date, s.write_uid, s.write_date,
            s.id, s.%s, s.guest_qty,
            r.group_id, r.user_id,
            s.group_id,
            s.arrival_date, s.arrival_time, s.arrival_datetime,
            s.departure_date, s.departure_time, s.departure_datetime,
            s.partner_id, s.partner_name, s.company_id
            FROM stay_stay s
            LEFT JOIN stay_room r ON r.id=s.%s
            WHERE s.%s IS NOT null
            """
            % (
                openupgrade.get_legacy_name("room_id"),
                openupgrade.get_legacy_name("room_id"),
                openupgrade.get_legacy_name("room_id"),
            ),
        )
    openupgrade.logged_query(env.cr, "UPDATE stay_stay SET state='confirm'")
    env["stay.stay"]._cron_stay_state_update()
    for stay in env["stay.stay"].search([("departure_date", ">=", datetime.today())]):
        msg = "Stay lines regenerated by Odoo v14 migration script"
        notes = "\n\n".join([x for x in (stay.notes, msg) if x])
        # This will re-generate the missing stay lines
        stay.write({"notes": notes})
