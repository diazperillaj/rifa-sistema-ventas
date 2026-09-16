from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.v1.dashboard import services
from app.api.v1.raffle.services import get_raffle
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.templates import templates
from app.models import User

router = APIRouter(tags=["dashboard"])


@router.get("/admin", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> HTMLResponse:
    raffle = get_raffle(db)
    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "raffle": raffle,
            "stats": services.get_stats(db, raffle.ticket_price),
            "latest": services.latest_sales(db),
            "sellers": services.sales_by_seller(db, raffle.ticket_price),
        },
    )
