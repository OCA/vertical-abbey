# Copyright 2017-2021 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStay(TransactionCase):
    def test_full_scenario(self):
        today = datetime.now().date()
        tomorrow = today + relativedelta(days=1)
        departure_date = tomorrow + relativedelta(days=3)
        new_departure_date = departure_date + relativedelta(days=1)
        refectory_id = self.env.ref("stay.refectory_ste_francoise").id
        stay1 = self.env["stay.stay"].create(
            {
                "arrival_date": tomorrow,
                "arrival_time": "afternoon",
                "departure_date": departure_date,
                "departure_time": "afternoon",
                "partner_name": "Toto",
                "guest_qty": 3,
                "refectory_id": refectory_id,
            }
        )
        self.assertEqual(stay1.state, "draft")
        stay1.draft2confirm()
        self.assertEqual(stay1.state, "confirm")
        self.assertEqual(len(stay1.line_ids), 4)
        self.assertEqual(min([line.date for line in stay1.line_ids]), tomorrow)
        self.assertEqual(max([line.date for line in stay1.line_ids]), departure_date)
        for line in stay1.line_ids:
            self.assertEqual(line.refectory_id.id, refectory_id)
            if line.date != departure_date:
                self.assertEqual(line.bed_night_qty, stay1.guest_qty)
        stay1.write({"arrival_date": today})
        self.assertEqual(stay1.state, "current")
        self.assertEqual(len(stay1.line_ids), 5)
        self.assertEqual(min([line.date for line in stay1.line_ids]), today)
        self.assertEqual(max([line.date for line in stay1.line_ids]), departure_date)
        stay1.write({"arrival_date": tomorrow, "departure_date": new_departure_date})
        self.assertEqual(stay1.state, "confirm")
        self.assertEqual(len(stay1.line_ids), 5)
        self.assertEqual(min([line.date for line in stay1.line_ids]), tomorrow)
        self.assertEqual(
            max([line.date for line in stay1.line_ids]), new_departure_date
        )
        with self.assertRaises(UserError):
            stay1.unlink()
        stay1.cancel()
        self.assertEqual(len(stay1.line_ids), 0)
        stay1.unlink()
