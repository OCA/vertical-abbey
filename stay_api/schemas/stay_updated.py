# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pydantic import BaseModel


class StayUpdated(BaseModel):
    name: str
    id: int
    phone: str | None = None
    mobile: str | None = None
    partner_id: int | None = None
