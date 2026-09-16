from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.auth import services
from app.api.v1.auth.schemas import LoginForm
from app.core.database import get_db
from app.core.dependencies import NotAuthenticated, get_current_user
from app.core.forms import form_data, validate_form
from app.core.templates import templates
from app.models import User

router = APIRouter(tags=["auth"])


def _render_login(request: Request, username: str = "", error: str | None = None, status_code: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "auth/login.html", {"username": username, "error": error}, status_code=status_code
    )


@router.get("/", include_in_schema=False)
def home(user: User = Depends(get_current_user)) -> RedirectResponse:
    return RedirectResponse("/admin" if user.is_admin else "/numeros", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    try:
        get_current_user(request, db)
        return RedirectResponse("/", status_code=303)
    except NotAuthenticated:
        return _render_login(request)


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, form: dict = Depends(form_data), db: Session = Depends(get_db)) -> HTMLResponse:
    data, _ = validate_form(LoginForm, form)
    username = form.get("username", "").strip()
    if data is None:
        return _render_login(request, username, "Ingresa usuario y contraseña", 400)

    throttle_key = f"{request.client.host if request.client else '-'}:{data.username}"
    if services.login_throttle.is_blocked(throttle_key):
        return _render_login(request, username, "Demasiados intentos. Espera unos minutos e inténtalo de nuevo.", 429)

    user = services.authenticate(db, data.username, data.password)
    if user is None:
        services.login_throttle.register_failure(throttle_key)
        return _render_login(request, username, "Usuario o contraseña incorrectos", 400)

    services.login_throttle.reset(throttle_key)
    services.login(request, user)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    services.logout(request)
    return RedirectResponse("/login", status_code=303)
