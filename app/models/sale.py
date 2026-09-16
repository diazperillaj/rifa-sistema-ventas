from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, SmallInteger, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from app.models.user import User

MIN_NUMBER = 0
MAX_NUMBER = 99
TOTAL_NUMBERS = MAX_NUMBER - MIN_NUMBER + 1


class Sale(CreatedAtMixin, UpdatedAtMixin, Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint(f"number BETWEEN {MIN_NUMBER} AND {MAX_NUMBER}", name="number_range"),
        Index("ix_sales_created_at", "created_at"),  # últimos vendidos
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(SmallInteger, unique=True, nullable=False)
    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    buyer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    buyer_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, server_default=false(), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    seller: Mapped["User"] = relationship(back_populates="sales")
