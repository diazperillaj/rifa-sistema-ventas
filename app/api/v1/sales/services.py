from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.v1.sales.schemas import SaleForm
from app.core.forms import FORM_ERROR
from app.models import Sale, User
from app.models.sale import MAX_NUMBER, MIN_NUMBER

NUMBER_TAKEN = "Este número ya fue vendido. Elige otro."


class SaleError(Exception):
    def __init__(self, message: str, field: str = FORM_ERROR) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


@dataclass
class SalesSummary:
    total: int
    paid: int
    collected: Decimal
    receivable: Decimal

    @property
    def pending(self) -> int:
        return self.total - self.paid


def is_sold(db: Session, number: int) -> bool:
    return db.scalar(select(Sale.id).where(Sale.number == number)) is not None


def available_numbers(db: Session) -> list[int]:
    sold = set(db.scalars(select(Sale.number)))
    return [n for n in range(MIN_NUMBER, MAX_NUMBER + 1) if n not in sold]


def get_sale_for_user(db: Session, sale_id: int, user: User) -> Sale | None:
    """Devuelve la venta solo si el usuario es el vendedor o es admin."""
    sale = db.get(Sale, sale_id)
    if sale is None or not (user.is_admin or sale.seller_id == user.id):
        return None
    return sale


def list_seller_sales(db: Session, seller: User) -> list[Sale]:
    return list(db.scalars(
        select(Sale).where(Sale.seller_id == seller.id).order_by(Sale.created_at.desc())
    ))


@dataclass
class SaleFilters:
    seller_id: int | None = None
    status: Literal["todos", "pagados", "pendientes"] = "todos"
    q: str = ""
    order: Literal["recientes", "numero"] = "recientes"

    @classmethod
    def from_params(cls, seller: str, status: str, q: str, order: str) -> "SaleFilters":
        """Valores inválidos en la URL se ignoran en vez de fallar."""
        return cls(
            seller_id=int(seller) if seller.isdigit() else None,
            status=status if status in ("pagados", "pendientes") else "todos",
            q=q.strip()[:60],
            order="numero" if order == "numero" else "recientes",
        )

    @property
    def active(self) -> bool:
        return self.seller_id is not None or self.status != "todos" or bool(self.q)


def list_sales(db: Session, filters: SaleFilters) -> list[Sale]:
    stmt = select(Sale).options(joinedload(Sale.seller))

    if filters.seller_id is not None:
        stmt = stmt.where(Sale.seller_id == filters.seller_id)
    if filters.status == "pagados":
        stmt = stmt.where(Sale.is_paid.is_(True))
    elif filters.status == "pendientes":
        stmt = stmt.where(Sale.is_paid.is_(False))

    if filters.q:
        # Sin distinguir mayúsculas ni tildes: "maria" encuentra "María"
        pattern = "%" + filters.q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        conditions = [func.unaccent(Sale.buyer_name).ilike(func.unaccent(pattern), escape="\\")]
        digits = filters.q.replace(" ", "")
        if digits.isdigit():
            conditions.append(func.replace(Sale.buyer_phone, " ", "").contains(digits, autoescape=True))
            if len(digits) <= 2:
                conditions.append(Sale.number == int(digits))
        stmt = stmt.where(or_(*conditions))

    if filters.order == "numero":
        stmt = stmt.order_by(Sale.number)
    else:
        stmt = stmt.order_by(Sale.created_at.desc(), Sale.id.desc())
    return list(db.scalars(stmt))


def list_sellers(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.full_name)))


def summarize(sales: list[Sale], ticket_price: Decimal) -> SalesSummary:
    paid = sum(1 for s in sales if s.is_paid)
    return SalesSummary(
        total=len(sales),
        paid=paid,
        collected=ticket_price * paid,
        receivable=ticket_price * (len(sales) - paid),
    )


def create_sale(db: Session, seller: User, data: SaleForm) -> Sale:
    sale = Sale(seller_id=seller.id, **data.model_dump())
    db.add(sale)
    _commit_unique_number(db)
    return sale


def update_sale(db: Session, sale: Sale, data: SaleForm) -> Sale:
    for field, value in data.model_dump().items():
        setattr(sale, field, value)
    _commit_unique_number(db)
    return sale


def toggle_paid(db: Session, sale: Sale) -> Sale:
    sale.is_paid = not sale.is_paid
    db.commit()
    return sale


def delete_sale(db: Session, sale: Sale) -> None:
    db.delete(sale)
    db.commit()


def _commit_unique_number(db: Session) -> None:
    # La restricción UNIQUE de la BD resuelve dos ventas simultáneas del mismo número
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "uq_sales_number" in str(exc.orig):
            raise SaleError(NUMBER_TAKEN, field="number") from exc
        raise
