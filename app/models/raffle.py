from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UpdatedAtMixin

RAFFLE_ID = 1


class Raffle(UpdatedAtMixin, Base):
    """Configuración de la rifa. Solo existe una fila (id = 1)."""

    __tablename__ = "raffle"
    __table_args__ = (CheckConstraint(f"id = {RAFFLE_ID}", name="single_row"),)

    id: Mapped[int] = mapped_column(primary_key=True, default=RAFFLE_ID)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    ticket_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    draw_date: Mapped[date | None] = mapped_column(Date)
