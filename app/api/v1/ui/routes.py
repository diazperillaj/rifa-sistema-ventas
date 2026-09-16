"""Vista previa de componentes. Solo se registra fuera de producción."""

from decimal import Decimal
from types import SimpleNamespace

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter(tags=["ui"])


@router.get("/ui", response_class=HTMLResponse)
def ui_preview(request: Request) -> HTMLResponse:
    request.state.user = SimpleNamespace(full_name="Laura Pérez", is_admin=True)
    sold = {3, 7, 12, 18, 21, 25, 33, 40, 41, 47, 52, 58, 64, 69, 70, 77, 81, 88, 90, 99}
    mine = {7, 21, 47, 70}
    sales = [
        {"number": 99, "buyer": "Carlos Gómez", "phone": "300 123 4567", "seller": "Laura", "paid": True, "time": "10:42"},
        {"number": 90, "buyer": "Ana María Ríos", "phone": "311 987 6543", "seller": "Luis", "paid": False, "time": "10:15"},
        {"number": 88, "buyer": "Pedro Díaz", "phone": "320 555 0101", "seller": "Laura", "paid": True, "time": "09:58"},
    ]
    return templates.TemplateResponse(
        request,
        "ui/preview.html",
        {
            "sold": sold,
            "mine": mine,
            "sales": sales,
            "ticket_price": Decimal("10000"),
        },
    )
