from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.sale import MAX_NUMBER, MIN_NUMBER


class SaleForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    error_messages: ClassVar[dict[str, str]] = {
        "number": "Número no válido",
    }

    number: int = Field(ge=MIN_NUMBER, le=MAX_NUMBER)
    buyer_name: str = Field(min_length=2, max_length=120)
    buyer_phone: str | None = Field(default=None, max_length=30)
    is_paid: bool = False  # checkbox sin marcar no se envía
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("buyer_phone", "notes", mode="before")
    @classmethod
    def empty_to_none(cls, value):
        return value.strip() or None if isinstance(value, str) else value
