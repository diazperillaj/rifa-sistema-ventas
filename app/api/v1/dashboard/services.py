from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Sale, User
from app.models.sale import TOTAL_NUMBERS


@dataclass
class DashboardStats:
    sold: int
    paid: int
    ticket_price: Decimal

    @property
    def available(self) -> int:
        return TOTAL_NUMBERS - self.sold

    @property
    def pending(self) -> int:
        return self.sold - self.paid

    @property
    def collected(self) -> Decimal:
        return self.ticket_price * self.paid

    @property
    def receivable(self) -> Decimal:
        return self.ticket_price * self.pending

    @property
    def expected_total(self) -> Decimal:
        return self.ticket_price * TOTAL_NUMBERS

    @property
    def progress(self) -> int:
        return round(self.sold * 100 / TOTAL_NUMBERS)


@dataclass
class SellerSummary:
    user: User
    total: int
    paid: int
    ticket_price: Decimal

    @property
    def collected(self) -> Decimal:
        return self.ticket_price * self.paid

    @property
    def receivable(self) -> Decimal:
        return self.ticket_price * (self.total - self.paid)


def get_stats(db: Session, ticket_price: Decimal) -> DashboardStats:
    sold, paid = db.execute(
        select(func.count(Sale.id), func.count(Sale.id).filter(Sale.is_paid))
    ).one()
    return DashboardStats(sold=sold, paid=paid, ticket_price=ticket_price)


def latest_sales(db: Session, limit: int = 10) -> list[Sale]:
    return list(db.scalars(
        select(Sale)
        .options(joinedload(Sale.seller))
        .order_by(Sale.created_at.desc(), Sale.id.desc())
        .limit(limit)
    ))


def sales_by_seller(db: Session, ticket_price: Decimal) -> list[SellerSummary]:
    """Vendedores activos (aunque no tengan ventas) e inactivos que sí vendieron."""
    total = func.count(Sale.id)
    stmt = (
        select(User, total, func.count(Sale.id).filter(Sale.is_paid))
        .outerjoin(Sale, Sale.seller_id == User.id)
        .group_by(User.id)
        .having(or_(total > 0, User.is_active))
        .order_by(total.desc(), User.full_name)
    )
    return [SellerSummary(user, t, p, ticket_price) for user, t, p in db.execute(stmt).all()]
