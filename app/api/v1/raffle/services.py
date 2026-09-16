from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.raffle.schemas import RaffleForm
from app.models import Raffle, Sale, User
from app.models.raffle import RAFFLE_ID
from app.models.sale import MAX_NUMBER, MIN_NUMBER, TOTAL_NUMBERS

CellStatus = Literal["available", "mine", "sold"]


@dataclass
class BoardCell:
    number: int
    status: CellStatus
    sale_id: int | None  # solo si el usuario puede abrir la venta (dueño o admin)


@dataclass
class Board:
    cells: list[BoardCell]
    sold: int
    mine: int

    @property
    def available(self) -> int:
        return TOTAL_NUMBERS - self.sold


def get_raffle(db: Session) -> Raffle:
    return db.get(Raffle, RAFFLE_ID)  # la fila la crea la migración inicial


def update_raffle(db: Session, data: RaffleForm) -> Raffle:
    raffle = get_raffle(db)
    raffle.name = data.name
    raffle.ticket_price = data.ticket_price
    raffle.draw_date = data.draw_date
    db.commit()
    return raffle


def get_board(db: Session, user: User) -> Board:
    sold = {number: (sale_id, seller_id) for number, sale_id, seller_id in
            db.execute(select(Sale.number, Sale.id, Sale.seller_id)).all()}

    cells: list[BoardCell] = []
    for number in range(MIN_NUMBER, MAX_NUMBER + 1):
        if number not in sold:
            cells.append(BoardCell(number, "available", None))
            continue
        sale_id, seller_id = sold[number]
        is_mine = seller_id == user.id
        cells.append(BoardCell(
            number,
            "mine" if is_mine else "sold",
            sale_id if is_mine or user.is_admin else None,
        ))

    return Board(cells=cells, sold=len(sold), mine=sum(c.status == "mine" for c in cells))
