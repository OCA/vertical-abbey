# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from pydantic import BaseModel


class StayRead(BaseModel):
    guest_qty: int
    arrival_date: date
    departure_date: date
    name: str
    lastname: str | None = None
    firstname: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    arrival_time: str | None = None
    arrival_note: str | None = None
    departure_time: str | None = None
    departure_note: str | None = None
    country_code: str | None = None
    street: str | None = None
    street2: str | None = None
    zip: str | None = None
    city: str | None = None
