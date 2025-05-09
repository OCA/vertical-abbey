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
    lastname: str = None
    firstname: str = None
    title: str = None
    email: str = None
    phone: str = None
    mobile: str = None
    arrival_time: str = None
    arrival_note: str = None
    departure_time: str = None
    departure_note: str = None
    country_code: str = None
    street: str = None
    street2: str = None
    zip: str = None
    city: str = None
