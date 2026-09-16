import re
from datetime import date
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RaffleForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    error_messages: ClassVar[dict[str, str]] = {
        "ticket_price": "Ingresa un valor válido, por ejemplo 10.000",
        "draw_date": "Ingresa una fecha válida",
    }

    name: str = Field(min_length=2, max_length=120)
    ticket_price: Decimal = Field(ge=0, max_digits=12, decimal_places=0)
    draw_date: date | None = None

    @field_validator("ticket_price", mode="before")
    @classmethod
    def clean_price(cls, value):
        # Acepta "10.000", "$ 10,000", "10000"
        if isinstance(value, str):
            digits = re.sub(r"[^\d]", "", value)
            return digits or value
        return value

    @field_validator("draw_date", mode="before")
    @classmethod
    def empty_date_to_none(cls, value):
        return value or None
