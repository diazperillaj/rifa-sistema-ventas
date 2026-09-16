from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import UserRole


class UserBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    error_messages: ClassVar[dict[str, str]] = {
        "username": "Usa de 3 a 50 caracteres: letras minúsculas, números, punto, guion o guion bajo",
    }

    full_name: str = Field(min_length=2, max_length=120)
    username: str = Field(pattern=r"^[a-z0-9._-]{3,50}$")
    phone: str | None = Field(default=None, max_length=30)
    role: UserRole = UserRole.SELLER

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("phone", mode="before")
    @classmethod
    def empty_phone_to_none(cls, value: str | None) -> str | None:
        return value.strip() or None if isinstance(value, str) else value


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(UserBase):
    is_active: bool = False  # checkbox sin marcar no se envía


class PasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=128)
