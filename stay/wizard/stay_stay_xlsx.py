# Copyright 2020-2021 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from io import BytesIO

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug("Can not import xlsxwriter`.")


class StayStayXlsx(models.TransientModel):
    _name = "stay.stay.xlsx"
    _description = "Print Stay Global view"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company_id = self.env.company.id
        today_dt = fields.Date.context_today(self)
        end_date_dt = today_dt + relativedelta(months=6, days=-1)
        groups = self.env["stay.group"].search(
            [
                ("user_id", "=", self.env.user.id),
                ("company_id", "=", company_id),
            ]
        )
        if not groups:
            groups = self.env["stay.group"].search([("company_id", "=", company_id)])
        res.update(
            {
                "start_date": today_dt,
                "end_date": end_date_dt,
                "group_ids": groups and groups.ids or [],
                "company_id": company_id,
            }
        )
        return res

    company_id = fields.Many2one("res.company", string="Company", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    group_ids = fields.Many2many(
        "stay.group", string="Groups", domain="[('company_id', '=', company_id)]"
    )
    file_xlsx = fields.Binary(readonly=True)
    filename = fields.Char(readonly=True)

    def prepare_tab(self):
        res = {}
        if not self.group_ids:
            # take everything
            res[_("All")] = self.env["stay.room"].search(
                [("company_id", "=", self.company_id.id)]
            )
        else:
            for group in self.group_ids:
                res[group.name] = group.room_ids
        return res

    def run(self):
        self.ensure_one()
        srao = self.env["stay.room.assign"]
        start_date_dt = self.start_date
        end_date_dt = self.end_date
        #        start_date_dt = fields.Date.from_string(start_date)
        #        end_date_dt = fields.Date.from_string(end_date)
        date_labels = self.env["stay.date.label"].search_read(
            [
                ("date", ">=", self.start_date),
                ("date", "<=", self.end_date),
                ("name", "!=", False),
            ],
            ["date", "name"],
        )
        date2label = {}
        for date_label in date_labels:
            date2label[date_label["date"]] = date_label["name"]
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        for group_name, rooms in self.prepare_tab().items():
            room2col = {}
            sheet = workbook.add_worksheet(group_name)
            sheet.set_column(0, 0, 22)
            sheet.set_column(1, 1, 16)
            sheet.set_row(0, 35)
            sheet.set_row(1, 25)
            title = workbook.add_format(
                {"bold": True, "font_size": 20, "align": "left", "valign": "vcenter"}
            )
            header_other = workbook.add_format(
                {
                    "bold": True,
                    "font_size": 12,
                    "align": "center",
                    "valign": "vcenter",
                    "bg_color": "#fff830",
                }
            )
            header_room = workbook.add_format(
                {
                    "bold": True,
                    "font_size": 12,
                    "align": "center",
                    "valign": "vcenter",
                    "bg_color": "#baf9ff",
                }
            )
            sunday_color = "#f7ffb0"
            font_size = 10
            regular_date = workbook.add_format(
                {
                    "num_format": "dddd d mmmm yyyy",
                    "align": "right",
                    "font_size": font_size,
                }
            )
            regular_date_sunday = workbook.add_format(
                {
                    "num_format": "dddd d mmmm yyyy",
                    "align": "right",
                    "bg_color": sunday_color,
                    "font_size": font_size,
                }
            )
            regular = workbook.add_format({"font_size": font_size, "align": "left"})
            regular_sunday = workbook.add_format(
                {"font_size": font_size, "bg_color": sunday_color, "align": "left"}
            )
            regular_stay = workbook.add_format(
                {"font_size": font_size, "align": "left", "bg_color": "#7eb7fc"}
            )
            i = 0
            sheet.write(i, 0, _("Stays - %s") % self.company_id.name, title)
            i += 1
            sheet.write(i, 0, _("Date"), header_other)
            sheet.write(i, 1, _("Celebration"), header_other)

            z = 2
            for room in rooms:
                room2col[room] = z
                sheet.set_column(z, z, 17)
                sheet.write(i, z, room.code or room.name, header_room)
                z += 1

            date_dt = start_date_dt
            date2row = {}
            while date_dt <= end_date_dt:
                i += 1
                date2row[date_dt] = i
                cell_style_date = regular_date
                cell_style = regular
                if date_dt.weekday() == 6:
                    cell_style_date = regular_date_sunday
                    cell_style = regular_sunday
                sheet.write(i, 0, date_dt, cell_style_date)
                sheet.write(i, 1, date2label.get(date_dt, ""), cell_style)
                for col in room2col.values():
                    sheet.write(i, col, "", cell_style)

                date_dt += relativedelta(days=1)
            for room in rooms:
                room_assigns = srao.search(
                    [
                        ("room_id", "=", room.id),
                        ("arrival_date", "<=", end_date_dt),
                        ("departure_date", ">=", start_date_dt),
                    ]
                )
                col = room2col[room]
                for assign in room_assigns:
                    nights_dt = []
                    stay_start_dt = assign.arrival_date
                    stay_end_dt = assign.departure_date
                    cell_label = assign.partner_name
                    stay_date_dt = stay_start_dt
                    while stay_date_dt < stay_end_dt:
                        nights_dt.append(stay_date_dt)
                        stay_date_dt += relativedelta(days=1)
                    for night_dt in nights_dt:
                        row = date2row.get(night_dt)
                        if row:
                            sheet.write(
                                date2row[night_dt], col, cell_label, regular_stay
                            )

        workbook.close()
        file_data.seek(0)
        filename = "Stay_%s.xlsx" % fields.Date.context_today(self)
        export_file_b64 = base64.encodebytes(file_data.read())
        self.write(
            {
                "filename": filename,
                "file_xlsx": export_file_b64,
            }
        )
        action = {
            "name": "Stay",
            "type": "ir.actions.act_url",
            "url": "web/content/?model=%s&id=%d&filename_field=filename&"
            "field=file_xlsx&download=true&filename=%s"
            % (self._name, self.id, self.filename),
            "target": "self",
        }
        return action
