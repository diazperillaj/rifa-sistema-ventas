from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.auth import services as auth_services
from app.api.v1.users import services
from app.api.v1.users.schemas import PasswordReset, UserCreate, UserUpdate
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.core.forms import form_data, validate_form
from app.core.templates import flash, templates
from app.models import User

router = APIRouter(prefix="/admin/usuarios", tags=["users"])

ROLE_OPTIONS = [("seller", "Vendedor"), ("admin", "Administrador")]


def _get_or_404(db: Session, user_id: int) -> User:
    user = services.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404)
    return user


def _render_form(
    request: Request,
    *,
    user: User | None = None,
    values: dict | None = None,
    errors: dict | None = None,
    password_errors: dict | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    values = {k: v for k, v in (values or {}).items() if k != "password"}
    return templates.TemplateResponse(
        request,
        "users/form.html",
        {
            "user": user,
            "values": values,
            "errors": errors or {},
            "password_errors": password_errors or {},
            "role_options": ROLE_OPTIONS,
        },
        status_code=status_code,
    )


def _values_from_user(user: User) -> dict:
    return {
        "full_name": user.full_name,
        "username": user.username,
        "phone": user.phone or "",
        "role": user.role.value,
        "is_active": user.is_active,
    }


@router.get("", response_class=HTMLResponse)
def list_users(request: Request, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> HTMLResponse:
    rows = services.list_users_with_sales(db)
    return templates.TemplateResponse(request, "users/list.html", {"rows": rows})


@router.get("/nuevo", response_class=HTMLResponse)
def new_user_page(request: Request, _: User = Depends(require_admin)) -> HTMLResponse:
    return _render_form(request, values={"role": "seller"})


@router.post("/nuevo", response_class=HTMLResponse)
def create_user(
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> HTMLResponse:
    data, errors = validate_form(UserCreate, form)
    if data is not None:
        try:
            user = services.create_user(db, data)
        except services.UserError as exc:
            errors = {exc.field: exc.message}
        else:
            flash(request, f"Usuario {user.username} creado")
            return RedirectResponse("/admin/usuarios", status_code=303)
    return _render_form(request, values=form, errors=errors, status_code=400)


@router.get("/{user_id}/editar", response_class=HTMLResponse)
def edit_user_page(
    user_id: int, request: Request, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> HTMLResponse:
    user = _get_or_404(db, user_id)
    return _render_form(request, user=user, values=_values_from_user(user))


@router.post("/{user_id}/editar", response_class=HTMLResponse)
def update_user(
    user_id: int,
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> HTMLResponse:
    user = _get_or_404(db, user_id)
    data, errors = validate_form(UserUpdate, form)
    if data is not None:
        try:
            services.update_user(db, user, data, acting_user=admin)
        except services.UserError as exc:
            errors = {exc.field: exc.message}
        else:
            flash(request, f"Usuario {user.username} actualizado")
            return RedirectResponse("/admin/usuarios", status_code=303)
    values = {**form, "is_active": "is_active" in form}
    return _render_form(request, user=user, values=values, errors=errors, status_code=400)


@router.post("/{user_id}/password", response_class=HTMLResponse)
def reset_password(
    user_id: int,
    request: Request,
    form: dict = Depends(form_data),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> HTMLResponse:
    user = _get_or_404(db, user_id)
    data, errors = validate_form(PasswordReset, form)
    if data is None:
        return _render_form(
            request, user=user, values=_values_from_user(user), password_errors=errors, status_code=400
        )

    services.set_password(db, user, data.password)
    if user.id == admin.id:
        auth_services.login(request, user)  # mantiene la sesión propia tras el cambio
    flash(request, f"Contraseña de {user.username} actualizada")
    return RedirectResponse("/admin/usuarios", status_code=303)
