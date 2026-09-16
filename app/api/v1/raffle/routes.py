from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.raffle import services
from app.api.v1.raffle.schemas import RaffleForm
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.core.forms import form_data, validate_form
from app.core.templates import flash, templates
from app.models import User

router = APIRouter(tags=["raffle"])


@router.get("/numeros", response_class=HTMLResponse)
def board_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "raffle/board.html",
        {"raffle": services.get_raffle(db), "board": services.get_board(db, user)},
    )


def _render_settings(request: Request, values: dict, errors: dict | None = None, status_code: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "raffle/settings.html", {"values": values, "errors": errors or {}}, status_code=status_code
    )


@router.get("/admin/rifa", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> HTMLResponse:
    raffle = services.get_raffle(db)
    return _render_settings(request, {
        "name": raffle.name,
        "ticket_price": f"{raffle.ticket_price:,.0f}".replace(",", "."),
        "draw_date": raffle.draw_date.isoformat() if raffle.draw_date else "",
    })


@router.post("/admin/rifa", response_class=HTMLResponse)
def update_settings(
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> HTMLResponse:
    data, errors = validate_form(RaffleForm, form)
    if data is None:
        return _render_settings(request, form, errors, status_code=400)
    services.update_raffle(db, data)
    flash(request, "Configuración de la rifa guardada")
    return RedirectResponse("/numeros", status_code=303)
