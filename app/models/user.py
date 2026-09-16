import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from app.models.sale import Sale


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SELLER = "seller"


class User(CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda roles: [r.value for r in roles],
        ),
        default=UserRole.SELLER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true(), nullable=False)

    sales: Mapped[list["Sale"]] = relationship(back_populates="seller")

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
