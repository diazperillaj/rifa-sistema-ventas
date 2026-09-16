from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.security import get_csrf_token

APP_DIR = Path(__file__).resolve().parent.parent
CSS_FILE = APP_DIR / "static" / "css" / "app.css"

FLASH_SESSION_KEY = "_flash"


def flash(request: Request, message: str, variant: Literal["success", "info", "warning", "danger"] = "success") -> None:
    """Mensaje que se muestra una sola vez en la siguiente página."""
    messages = request.session.get(FLASH_SESSION_KEY, [])
    messages.append({"message": message, "variant": variant})
    request.session[FLASH_SESSION_KEY] = messages


def app_context(request: Request) -> dict:
    return {
        "current_user": getattr(request.state, "user", None),
        "csrf_token": get_csrf_token(request),
        "flashes": request.session.pop(FLASH_SESSION_KEY, []),
    }


templates = Jinja2Templates(directory=APP_DIR / "templates", context_processors=[app_context])


TZ = ZoneInfo(settings.timezone)
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def format_datetime(value: datetime) -> str:
    """16/09/2026 · 10:42 am (hora local)"""
    local = value.astimezone(TZ)
    return local.strftime("%d/%m/%Y · %I:%M ") + ("am" if local.hour < 12 else "pm")


def format_date(value: date) -> str:
    """20 de diciembre de 2026"""
    return f"{value.day} de {MONTHS[value.month - 1]} de {value.year}"


def format_number(value: int) -> str:
    """07, 42, 99"""
    return f"{value:02d}"


def format_money(value: Decimal | int | float) -> str:
    """$ 10.000"""
    return "$ " + f"{value:,.0f}".replace(",", ".")


def nav_items(user) -> list[dict[str, str]]:
    items = [
        {"label": "Números", "href": "/numeros"},
        {"label": "Mis ventas", "href": "/mis-ventas"},
    ]
    if user is not None and user.is_admin:
        items += [
            {"label": "Panel", "href": "/admin"},
            {"label": "Ventas", "href": "/admin/ventas"},
            {"label": "Usuarios", "href": "/admin/usuarios"},
        ]
    return items


def is_active(path: str, href: str) -> bool:
    if href == "/admin":
        return path == href
    return path == href or path.startswith(href + "/")


templates.env.filters["number"] = format_number
templates.env.filters["money"] = format_money
templates.env.filters["datetime"] = format_datetime
templates.env.filters["date"] = format_date
templates.env.globals["nav_items"] = nav_items
templates.env.globals["is_active"] = is_active
# Evita que el navegador use un CSS viejo después de un despliegue
templates.env.globals["static_version"] = int(CSS_FILE.stat().st_mtime) if CSS_FILE.exists() else 0
